from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pydantic.alias_generators import to_camel

from auth.auth import UserInfo
from routers.json_response import json_response
from sql_interface import crud
from sql_interface.database import get_db


router = APIRouter()


@router.get("/tags")
def read_tags(
    user_info: UserInfo,
    partialName: str = "",
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    get_tag_result = crud.get_tags(db, partialName, offset, limit)

    tags = []
    for db_tag in get_tag_result.tags:
        tags.append({
            "id": db_tag.id,
            "name": db_tag.name,
        })
    tags.sort(key=lambda x: x["id"])
    return json_response({
        "tagsCountAll": get_tag_result.tags_count,
        "users": tags,
    })


class CreateTagReqParams(BaseModel):
    name: str

    class Config:
        alias_generator = to_camel


@router.post("/tags")
def create_tag(
    user_info: UserInfo,
    params: CreateTagReqParams,
    db: Session = Depends(get_db),
):
    db_tag = crud.get_tag_by_name(db, params.name)
    if db_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specified name already exists."
        )
    created_tag = crud.create_tag(db, params.name)

    return json_response({
        "id": created_tag.id,
        "name": created_tag.name,
    })
