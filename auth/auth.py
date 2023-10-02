import datetime
from typing import Union
from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from sql_interface import crud, schemas
from sql_interface.database import get_db
from auth.jwt import encode_access_token, decode_access_token


ACCESS_TOKEN_EXPIRE_MINUTES = 30


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")

auth_router = APIRouter()


# token api
@auth_router.post("/auth")
async def get_token(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends()
    ],
    db: Session = Depends(get_db),
):
    user = crud.get_user(
        db,
        id=form_data.username,
        password=form_data.password
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return {
        "accessToken": encode_access_token(
            user.id,
            datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        ),
        "tokenType": "bearer",
    }


# intermediate function for auth check
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if user_id is None:
        # malformatted token
        raise credentials_exception
    
    user = crud.get_user(db, id=user_id)
    if user is None:
        # user not found
        raise credentials_exception
    
    return user


# add this to route arguments in order to check token
UserInfo = Annotated[
    Union[schemas.UserReadDeep, None],
    Depends(get_current_user)
]
