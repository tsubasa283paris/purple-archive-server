from typing import List

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pydantic.alias_generators import to_camel

from auth.auth import UserInfo
from routers.json_response import json_response
from sql_interface import crud
from sql_interface.database import get_db


router = APIRouter()


class AddBookmarksReqParams(BaseModel):
    album_ids: List[int]

    class Config:
        alias_generator = to_camel


@router.post("/users/me/bookmarks")
def add_bookmarks(
    user_info: UserInfo,
    params: AddBookmarksReqParams,
    db: Session = Depends(get_db),
):
    return json_response({
        "albumIds": crud.add_bookmarks(
            db, user_info.id, params.album_ids
        ),
    })


class RemoveBookmarksReqParams(BaseModel):
    album_ids: List[int]

    class Config:
        alias_generator = to_camel


@router.post("/users/me/bookmarks/unbookmark")
def remove_bookmarks(
    user_info: UserInfo,
    params: RemoveBookmarksReqParams,
    db: Session = Depends(get_db),
):
    return json_response({
        "albumIds": crud.remove_bookmarks(
            db, user_info.id, params.album_ids
        ),
    })
