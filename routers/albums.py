import base64
import binascii
import datetime
import os
import hashlib
import uuid
from typing import Dict, List

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


router = APIRouter()


def get_gif_path(uuid: str) -> str:
    return os.path.join(TEMP_DIR_NAME, f"{uuid}.gif")


def temp_to_storage_path(temp_path: str) -> str:
    return temp_path.replace(TEMP_DIR_NAME, STORAGE_DIR_NAME)


def serialize_album(album: models.Album) -> Dict:
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
                "text": tag.text,
            } for tag in album.tags
        ],
        "pageMetaData": [
            {
                "description": page.description,
                "playerName": page.player_name,
            } for page in album.pages
        ],
        "created_at": album.created_at,
        "updated_at": album.updated_at,
    }


@router.get("/albums")
def read_albums(
    user_info: UserInfo,
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    db_albums = crud.get_albums(db, offset=offset, limit=limit)
    return {
        "albumsCountAll": len(db_albums),
        "albums": [
            {
                "id": db_album.id,
                "source": db_album.source,
                "pvCount": db_album.pv_count,
                "downloadCount": db_album.download_count,
                "bookmarkCount": len(db_album.bookmark_users),
                "pageCount": len(db_album.pages),
                "playedAt": db_album.played_at,
                "createdAt": db_album.created_at,
                "updatedAt": db_album.updated_at,
            } for db_album in db_albums
        ]
    }


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
