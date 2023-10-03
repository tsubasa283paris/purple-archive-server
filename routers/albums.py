import base64
import binascii
import os
import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.auth import UserInfo
from ocr.gif import load_gif_images
from pydantic import BaseModel
from sql_interface import crud, schemas
from sql_interface.database import get_db


TEMP_DIR_NAME = "temp_albums"


router = APIRouter()


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
    temp_file_path = os.path.join(TEMP_DIR_NAME, f"{uuid_str}.gif")
    with open(temp_file_path, "wb") as f:
        f.write(raw_data)

    # load file contents
    # TODO: try except
    try:
        page_images = load_gif_images(temp_file_path)
    except NotImplementedError:
        # remove temporary file
        os.remove(temp_file_path)

        # raise invalid data error
        raise invalid_data_exception
    
    # call Google Vision API annotations
    # TODO
    dummy_ocr_results = [
        {
            "d": "dog",
            "p": "Alice",
        },
        {
            "d": "",
            "p": "Bob",
        },
        {
            "d": "cat",
            "p": "Cassidy",
        },
    ]
    
    # check if any album with the same hash value exist
    # (just check, no exception here)
    db_album = crud.get_album_by_hash(db, hash_str)
    
    # save temp_album data
    crud.create_temp_album(
        db,
        schemas.TempAlbumWrite(
            uuid=uuid_str,
            page_count=len(page_images)
        )
    )

    # all green
    return {
        "temporaryAlbumUuid": uuid_str,
        "hashMatchResult": db_album.id if db_album is not None else None,
        "pageMetaData": [
                {
                    "description": ocr_result["d"],
                    "playerName": ocr_result["p"],
                } for ocr_result in dummy_ocr_results
        ],
    }
