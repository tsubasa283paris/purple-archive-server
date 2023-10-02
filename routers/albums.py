from typing import List

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from auth.auth import UserInfo
from sql_interface import crud, schemas
from sql_interface.database import get_db


router = APIRouter()


@router.get("/albums/", response_model=List[schemas.AlbumRead])
def read_items(
    user_info: UserInfo,
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    items = crud.get_albums(db, offset=offset, limit=limit)
    return items
