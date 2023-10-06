from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session

from auth.auth import UserInfo
from sql_interface import crud, schemas
from sql_interface.database import get_db


router = APIRouter()


@router.get("/users")
def read_users(
    user_info: UserInfo,
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    get_users_result = crud.get_users(db, offset=offset, limit=limit)

    users = []
    for db_user in get_users_result.users:
        users.append({
            "id": db_user.id,
            "displayName": db_user.display_name,
            "createdAt": db_user.created_at,
            "updatedAt": db_user.updated_at,
        })
    users.sort(key=lambda x: x["id"])
    return {
        "usersCountTotal": get_users_result.users_count,
        "users": users,
    }


@router.get("/users/me")
def read_user_me(
    user_info: UserInfo,
):
    return {
        "id": user_info.id,
        "displayName": user_info.display_name,
        "createdAt": user_info.created_at,
        "updatedAt": user_info.updated_at,
    }


@router.get("/users/{user_id}")
def read_user(
    user_info: UserInfo,
    user_id: int,
    db: Session = Depends(get_db)
):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="Specified user does not exist."
        )
    return {
        "id": db_user.id,
        "displayName": db_user.display_name,
        "createdAt": db_user.created_at,
        "updatedAt": db_user.updated_at,
    }


@router.post("/users")
def create_user(
    user_info: UserInfo,
    user: schemas.UserWrite,
    db: Session = Depends(get_db)
):
    db_user = crud.get_user(db, id=user.id)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Specified user ID already exists."
        )
    created_user = crud.create_user(db=db, user=user)

    return {
        "id": created_user.id,
        "displayName": created_user.display_name,
        "createdAt": created_user.created_at,
        "updatedAt": created_user.updated_at,
    }
