import base64
import binascii
import datetime
import os
import hashlib
import uuid
from typing import Dict, List, Literal, Union

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.auth import UserInfo
from ocr.gif import GifManager
from ocr.image_annotator import annotate_images
from pydantic import BaseModel
from pydantic.alias_generators import to_camel
from sql_interface import crud, models, schemas
from sql_interface.database import get_db
from storage.s3 import upload


TEMP_DIR_NAME = "temp_albums"
STORAGE_DIR_NAME = "albums/v1"

GET_ALBUMS_ORDER_BY_PAT_STR = "playedAt"
GET_ALBUMS_ORDER_BY_PVC_STR = "pvCount"
GET_ALBUMS_ORDER_BY_DLC_STR = "downloadCount"
GET_ALBUMS_ORDER_BY_BMC_STR = "bookmarkCount"
GET_ALBUMS_ORDER_BY_PGC_STR = "pageCount"

def ga_orderby_str_to_en(s: str):
    if s == GET_ALBUMS_ORDER_BY_PAT_STR:
        return crud.GET_ALBUMS_ORDER_BY_PAT
    elif s == GET_ALBUMS_ORDER_BY_PVC_STR:
        return crud.GET_ALBUMS_ORDER_BY_PVC
    elif s == GET_ALBUMS_ORDER_BY_DLC_STR:
        return crud.GET_ALBUMS_ORDER_BY_DLC
    elif s == GET_ALBUMS_ORDER_BY_BMC_STR:
        return crud.GET_ALBUMS_ORDER_BY_BMC
    elif s == GET_ALBUMS_ORDER_BY_PGC_STR:
        return crud.GET_ALBUMS_ORDER_BY_PGC
    else:
        raise ValueError()

GET_ALBUMS_ORDER_ASC_STR = "asc"
GET_ALBUMS_ORDER_DESC_STR = "desc"

def ga_order_str_to_en(s: str):
    if s == GET_ALBUMS_ORDER_ASC_STR:
        return crud.GET_ALBUMS_ORDER_ASC
    elif s == GET_ALBUMS_ORDER_DESC_STR:
        return crud.GET_ALBUMS_ORDER_DESC
    else:
        raise ValueError()

router = APIRouter()


def get_gif_path(uuid: str) -> str:
    return os.path.join(TEMP_DIR_NAME, f"{uuid}.gif")


def temp_to_storage_path(temp_path: str) -> str:
    return temp_path.replace(TEMP_DIR_NAME, STORAGE_DIR_NAME)


def serialize_album(album: models.Album) -> Dict:
    sorted_tags = sorted(album.tags, key=lambda x: x.id)
    sorted_pages = sorted(album.pages, key=lambda x: x.index)
    return {
        "id": album.id,
        "source": album.source,
        "thumbSource": album.thumb_source,
        "pvCount": album.pv_count,
        "downloadCount": album.download_count,
        "bookmarkCount": len(album.bookmark_users),
        "pageCount": len(album.pages),
        "playedAt": album.played_at,
        "contributorUserId": album.contributor_user_id,
        "gamemodeId": album.gamemode_id,
        "tags": [
            {
                "id": tag.id,
                "name": tag.name,
            } for tag in sorted_tags
        ],
        "pageMetaData": [
            {
                "description": page.description,
                "playerName": page.player_name,
            } for page in sorted_pages
        ],
        "created_at": album.created_at,
        "updated_at": album.updated_at,
    }


@router.get("/albums")
def read_albums(
    user_info: UserInfo,
    partialDescription: Union[str, None] = None,
    partialPlayerName: Union[str, None] = None,
    playedFrom: Union[int, None] = None,
    playedUntil: Union[int, None] = None,
    gamemodeId: Union[int, None] = None,
    partialTag: Union[str, None] = None,
    myBookmark: Union[str, None] = None,
    offset: int = 0,
    limit: int = 100,
    orderBy: str = GET_ALBUMS_ORDER_BY_PAT_STR,
    order: str = GET_ALBUMS_ORDER_DESC_STR,
    db: Session = Depends(get_db)
):
    # validate orderBy and order strings
    try:
        order_by_en = ga_orderby_str_to_en(orderBy)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter orderBy is invalid.",
        )
    try:
        order_en = ga_order_str_to_en(order)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter order is invalid.",
        )
    
    get_albums_result = crud.get_albums(db)

    # filter
    filtered_db_albums: List[models.Album] = []
    for db_album in get_albums_result.albums:
        matched = True
        pages: List[models.Page] = db_album.pages
        tags: List[models.Tag] = db_album.tags
        bookmark_users: List[models.User] = db_album.bookmark_users

        if partialDescription is not None:
            pd_matched = False
            for page in pages:
                if partialDescription in page.description:
                    pd_matched = True
                    break
            matched &= pd_matched

        if partialPlayerName is not None:
            pp_matched = False
            for page in pages:
                if partialPlayerName in page.player_name:
                    pp_matched = True
                    break
            matched &= pp_matched

        if playedFrom is not None:
            played_from_dt = datetime.datetime \
                                .fromtimestamp(playedFrom).astimezone()
            matched &= db_album.played_at >= played_from_dt

        if playedUntil is not None:
            played_until_dt = datetime.datetime \
                                .fromtimestamp(playedUntil).astimezone()
            matched &= db_album.played_at <= played_until_dt

        if gamemodeId is not None:
            matched &= db_album.gamemode_id == gamemodeId
        
        if partialTag is not None:
            pt_matched = False
            for tag in tags:
                if partialTag in tag.name:
                    pt_matched = True
                    break
            matched &= pt_matched
        
        if myBookmark is not None and len(myBookmark):
            # any string is treated as myBookmark=true
            is_bookmarked = False
            for bookmark_user in bookmark_users:
                if bookmark_user.id == user_info.id:
                    is_bookmarked = True
                    break
            matched &= is_bookmarked
        
        # finally, move it to filtered list when all conditions green
        if matched:
            filtered_db_albums.append(db_album)
    
    total_count = len(filtered_db_albums)

    # sort, offset and limit
    sort_key = lambda a: a.played_at
    if order_by_en == crud.GET_ALBUMS_ORDER_BY_PVC:
        sort_key = lambda a: a.pv_count
    elif order_by_en == crud.GET_ALBUMS_ORDER_BY_DLC:
        sort_key = lambda a: a.download_count
    elif order_by_en == crud.GET_ALBUMS_ORDER_BY_BMC:
        sort_key = lambda a: len(a.bookmark_users)
    elif order_by_en == crud.GET_ALBUMS_ORDER_BY_PGC:
        sort_key = lambda a: len(a.pages)
    db_albums = sorted(
        filtered_db_albums, 
        key=sort_key,
        reverse=(order_en == crud.GET_ALBUMS_ORDER_DESC)
    )[offset : offset + limit]
    
    # create map of bookmarked or not by the user
    is_bookmarked_map: Dict[int, bool] = {}
    for bookmark_album in user_info.bookmark_albums:
        is_bookmarked_map[bookmark_album.id] = True
        
    return {
        "albumsCountAll": total_count,
        "albums": [
            {
                "id": db_album.id,
                "source": db_album.source,
                "thumbSource": db_album.thumb_source,
                "pvCount": db_album.pv_count,
                "downloadCount": db_album.download_count,
                "bookmarkCount": len(db_album.bookmark_users),
                "pageCount": len(db_album.pages),
                "isBookmarked": is_bookmarked_map.get(db_album.id) \
                                    is not None,
                "playedAt": db_album.played_at,
                "createdAt": db_album.created_at,
                "updatedAt": db_album.updated_at,
            } for db_album in db_albums
        ]
    }


@router.get("/albums/{album_id}")
def read_album(
    user_info: UserInfo,
    album_id: int,
    incrementPv: str = "",
    db: Session = Depends(get_db)
):
    db_album = crud.get_album(
        db, id=album_id, pv_increment=bool(len(incrementPv))
    )
    if db_album is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified album does not exist."
        )
    return serialize_album(db_album)


class CreateAlbumReqParams(BaseModel):
    temporary_album_uuid: str
    gamemode_id: int
    tag_ids: List[int]
    played_at: str
    page_meta_data: List[schemas.PageMetaData]

    class Config:
        alias_generator = to_camel


@router.post("/albums")
def create_album(
    user_info: UserInfo,
    params: CreateAlbumReqParams,
    db: Session = Depends(get_db)
):
    # check if specified temp album exists
    db_temp_album = crud.get_temp_album(db, params.temporary_album_uuid)
    if db_temp_album is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified temporaryAlbumUuid does not exist."
        )
    
    # validate page length
    if len(params.page_meta_data) != db_temp_album.page_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Length of pageMetaData does not match the specified " \
                    + "temporary album."
        )

    # validate gamemode
    db_gamemode = crud.get_gamemode(db, params.gamemode_id)
    if db_gamemode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified gamemodeId does not exist."
        )

    # validate tags
    for tag_id in params.tag_ids:
        db_tag = crud.get_tag(db, tag_id)
        if db_tag is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified tagIds involves tag(s) that do not exist."
            )
    
    # validate played_at
    iso_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Given datetime string does not match ISO format."
    )
    try:
        played_at_dt = datetime.datetime.fromisoformat(params.played_at)
    except ValueError:
        raise iso_exception
    if played_at_dt.tzname() is None:
        # doesn't allow TZ-unaware ISO format
        raise iso_exception
    
    # generate thumbnail file
    file_path = get_gif_path(params.temporary_album_uuid)
    thumb_path = file_path.replace(".gif", "_thumb.gif")
    gif = GifManager(file_path)
    gif.save_thumb(thumb_path)
    
    # upload original and thumb to S3 bucket
    s3_uri = upload(
        file_path,
        temp_to_storage_path(file_path)
    )
    s3_thumb_uri = upload(
        thumb_path,
        temp_to_storage_path(thumb_path)
    )

    # remove temporary files
    os.remove(file_path)
    os.remove(thumb_path)

    # save to database
    db_album = crud.create_album(
        db, params.temporary_album_uuid, params.gamemode_id,
        params.tag_ids, params.page_meta_data,
        s3_uri, s3_thumb_uri, db_temp_album.hash, user_info.id,
        played_at_dt
    )

    return serialize_album(db_album)


class CreateTempAlbumReqParams(BaseModel):
    data: str


@router.post("/albums/temp")
def create_temp_album(
    user_info: UserInfo,
    params: CreateTempAlbumReqParams,
    db: Session = Depends(get_db)
):
    invalid_data_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Given data cannot be interpreted as a base64 encoded " \
                + "GIF file.",
    )
    try:
        raw_data = base64.b64decode(params.data, validate=True)
    except binascii.Error:
        # base64 decode error
        raise invalid_data_exception
    
    # calculate hash value for this byte array
    hasher = hashlib.sha256()
    hasher.update(raw_data)
    hash_str = hasher.hexdigest()

    # generate uuid for this data
    uuid_str = str(uuid.uuid4())

    # save a temporary file server-side
    os.makedirs(TEMP_DIR_NAME, exist_ok=True)
    temp_file_path = get_gif_path(uuid_str)
    with open(temp_file_path, "wb") as f:
        f.write(raw_data)

    # load file contents
    gif = GifManager(temp_file_path)
    if len(gif.images) <= 1:
        print("Received too short data as GIF:", len(gif.images))
        # remove temporary file
        os.remove(temp_file_path)

        raise invalid_data_exception
    
    # call Google Vision API annotations
    ocr_results = annotate_images(gif.images)
    
    # check if any album with the same hash value exist
    # (just check, no exception here)
    db_album = crud.get_album_by_hash(db, hash_str)
    
    # save temp_album data
    crud.create_temp_album(
        db,
        schemas.TempAlbumWrite(
            uuid=uuid_str,
            page_count=len(gif.images),
            hash=hash_str
        )
    )

    # all green
    return {
        "temporaryAlbumUuid": uuid_str,
        "hashMatchResult": db_album.id if db_album is not None else None,
        "pageMetaData": [
            {
                "description": ocr_result.description,
                "playerName": ocr_result.player_name,
            } for ocr_result in ocr_results
        ],
    }


class UpdateAlbumReqParams(BaseModel):
    gamemode_id: int
    tag_ids: List[int]
    page_meta_data: List[schemas.PageMetaData]

    class Config:
        alias_generator = to_camel


@router.put("/albums/{album_id}")
def update_album(
    user_info: UserInfo,
    album_id: int,
    params: UpdateAlbumReqParams,
    db: Session = Depends(get_db)
):
    # check if album exists
    db_album = crud.get_album(
        db, id=album_id, pv_increment=False
    )
    if db_album is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified album does not exist."
        )

    # validate page length
    if len(params.page_meta_data) != len(db_album.pages):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Length of pageMetaData does not match the specified " \
                    + "album."
        )

    # validate gamemode
    db_gamemode = crud.get_gamemode(db, params.gamemode_id)
    if db_gamemode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified gamemodeId does not exist."
        )

    # validate tags
    for tag_id in params.tag_ids:
        db_tag = crud.get_tag(db, tag_id)
        if db_tag is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified tagIds involves tag(s) that do not exist."
            )
    
    # conduct update
    db_album = crud.update_album(
        db, db_album.id, params.gamemode_id,
        params.tag_ids, params.page_meta_data
    )

    return serialize_album(db_album)


@router.delete("/albums/{album_id}")
def delete_album(
    user_info: UserInfo,
    album_id: int,
    db: Session = Depends(get_db)
):
    # (this crud function ensures that the album.deleted_at is null)
    db_album = crud.get_album(db, album_id, pv_increment=False)
    if db_album is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified album does not exist."
        )
    
    # conduct soft-delete
    crud.soft_delete_album(db, album_id)

    return {}


@router.post("/albums/{album_id}/dlcount")
def increment_album_dlcount(
    user_info: UserInfo,
    album_id: int,
    db: Session = Depends(get_db)
):
    db_album = crud.get_album(db, album_id, pv_increment=False)
    if db_album is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified album does not exist."
        )
    
    # increment dl_count
    db_album = crud.increment_album_dlcount(db, album_id)

    return serialize_album(db_album)
