from typing import List

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session

from auth.auth import UserInfo
from sql_interface import crud, schemas
from sql_interface.database import get_db


router = APIRouter()


@router.get("/users", response_model=List[schemas.UserRead])
def read_users(
    user_info: UserInfo,
    offset: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
):
    users = crud.get_users(db, offset=offset, limit=limit)
    return users


@router.get("/users/me", response_model=schemas.UserReadDeep)
def read_user_me(
    user_info: UserInfo,
):
    return user_info


@router.get("/users/{user_id}", response_model=schemas.UserReadDeep)
def read_user(
    user_info: UserInfo,
    user_id: int,
    db: Session = Depends(get_db)
):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Specified user does not exist.")
    return db_user


@router.post("/users", response_model=schemas.UserRead)
def create_user(
    user_info: UserInfo,
    user: schemas.UserWrite,
    db: Session = Depends(get_db)
):
    db_user = crud.get_user(db, id=user.id)
    if db_user:
        raise HTTPException(status_code=400, detail="User ID already registered.")
    return crud.create_user(db=db, user=user)
