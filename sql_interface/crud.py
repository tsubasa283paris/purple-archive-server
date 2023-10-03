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
                models.User.deleted_at == None
            ) \
            .first()
    else:
        return db.query(models.User) \
            .filter(
                models.User.id == id,
                models.User.password == password,
                models.User.deleted_at == None
            ) \
            .first()


def get_users(db: Session, offset: int = 0, limit: int = 100):
    return db.query(models.User) \
        .filter(models.User.deleted_at == None) \
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

def get_album_by_hash(db: Session, hash_str: str):
    return db.query(models.Album) \
        .filter(models.Album.hash == hash_str) \
        .first()

# ----------------------------------------------------------------
# temp_album
# ----------------------------------------------------------------

def create_temp_album(db: Session, temp_album: schemas.TempAlbumWrite):
    db_temp_album = models.TempAlbum(
        uuid=temp_album.uuid,
        page_count=temp_album.page_count,
    )
    db.add(db_temp_album)
    db.commit()
    db.refresh(db_temp_album)
    return db_temp_album
