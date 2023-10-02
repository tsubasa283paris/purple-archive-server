from typing import List

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from auth.auth import UserInfo
from sql_interface import crud, schemas
from sql_interface.database import get_db


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
