from typing import Union

from sqlalchemy.orm import Session

from . import models, schemas


# ----------------------------------------------------------------
# user
# ----------------------------------------------------------------

def get_user(db: Session, id: str, password: Union[str, None] = None):
    if password is None:
        return db.query(models.User) \
            .filter(
                models.User.id == id,
            ) \
            .first()
    else:
        return db.query(models.User) \
            .filter(
                models.User.id == id,
                models.User.password == password,
            ) \
            .first()


def get_users(db: Session, offset: int = 0, limit: int = 100):
    return db.query(models.User) \
        .offset(offset) \
        .limit(limit) \
        .all()


def create_user(db: Session, user: schemas.UserWrite):
    db_user = models.User(
        id=user.id,
        password=user.password,
        display_name=user.display_name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ----------------------------------------------------------------
# album
# ----------------------------------------------------------------

def get_albums(db: Session, offset: int = 0, limit: int = 100):
    return db.query(models.Album) \
        .offset(offset) \
        .limit(limit) \
        .all()
