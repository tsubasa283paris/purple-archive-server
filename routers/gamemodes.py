from typing import List

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session

from auth.auth import UserInfo
from pydantic import BaseModel
from pydantic.alias_generators import to_camel
from sql_interface import crud, schemas
from sql_interface.database import get_db


router = APIRouter()


@router.get("/gamemodes")
def read_gamemodes(
    user_info: UserInfo,
    partialName: str = "",
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    get_gamemode_result = crud.get_gamemodes(db, partialName, offset, limit)

    gamemodes = []
    for db_gamemode in get_gamemode_result.gamemodes:
        gamemodes.append({
            "id": db_gamemode.id,
            "name": db_gamemode.name,
        })
    gamemodes.sort(key=lambda x: x["id"])
    return {
        "gamemodesCountAll": get_gamemode_result.gamemodes_count,
        "users": gamemodes,
    }


class CreateGamemodeReqParams(BaseModel):
    name: str

    class Config:
        alias_generator = to_camel


@router.post("/gamemodes")
def create_gamemodes(
    user_info: UserInfo,
    params: CreateGamemodeReqParams,
    db: Session = Depends(get_db),
):
    db_gamemode = crud.get_gamemode_by_name(db, params.name)
    if db_gamemode:
        raise HTTPException(
            status_code=400,
            detail="Specified name already exists."
        )
    created_gamemode = crud.create_gamemode(db, params.name)

    return {
        "id": created_gamemode.id,
        "name": created_gamemode.name,
    }


@router.delete("/gamemodes/{gamemode_id}")
def delete_gamemodes(
    user_info: UserInfo,
    gamemode_id: int,
    db: Session = Depends(get_db),
):
    db_gamemode = crud.get_gamemode(db, gamemode_id)
    if db_gamemode is None:
        raise HTTPException(
            status_code=404,
            detail="Specified gamemode does not exist."
        )
    crud.delete_gamemode(db, gamemode_id)

    return {}
