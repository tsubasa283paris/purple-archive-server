import datetime
from typing import List, Union

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
        .filter(models.Album.deleted_at == None) \
        .offset(offset) \
        .limit(limit) \
        .all()

def get_album_by_hash(db: Session, hash_str: str):
    return db.query(models.Album) \
        .filter(
            models.Album.hash == hash_str,
            models.Album.deleted_at == None,
        ) \
        .first()


def create_album(
    db: Session, temp_uuid: str, gamemode_id: int,
    tag_ids: List[int], page_meta_data: List[schemas.PageMetaData],
    source: str, thumb_source: str, hash: str, contributor_user_id: str,
    played_at: datetime.datetime
):
    # first, create album record
    db_album = models.Album(
        source=source,
        thumb_source=thumb_source,
        hash=hash,
        contributor_user_id=contributor_user_id,
        gamemode_id=gamemode_id,
        played_at=played_at
    )
    db.add(db_album)

    # create album-tag relations
    for tag_id in tag_ids:
        db_tag = get_tag(db, tag_id)
        db_album.tags.append(db_tag)
        db_tag.albums.append(db_album)
    
    # create page records
    for i, page in enumerate(page_meta_data):
        db_page = models.Page(
            album_id=db_album.id,
            index=i,
            description=page.description,
            player_name=page.player_name,
        )
        db.add(db_page)
        db_album.pages.append(db_page)
    
    # soft-delete temp_album record
    db_temp_album = get_temp_album(db, temp_uuid)
    db_temp_album.deleted_at = datetime.datetime.now().astimezone()

    db.commit()
    db.refresh(db_album)

    return db_album


# ----------------------------------------------------------------
# game_mode
# ----------------------------------------------------------------

def get_gamemode(db: Session, id: int):
    return db.query(models.Gamemode) \
        .filter(models.Gamemode.id == id) \
        .first()


# ----------------------------------------------------------------
# tag
# ----------------------------------------------------------------

def get_tag(db: Session, id: int):
    return db.query(models.Tag) \
        .filter(models.Tag.id == id) \
        .first()


# ----------------------------------------------------------------
# temp_album
# ----------------------------------------------------------------

def get_temp_album(db: Session, uuid: str):
    return db.query(models.TempAlbum) \
        .filter(
            models.TempAlbum.uuid == uuid,
            models.TempAlbum.deleted_at == None,
        ) \
        .first()

def create_temp_album(db: Session, temp_album: schemas.TempAlbumWrite):
    db_temp_album = models.TempAlbum(
        uuid=temp_album.uuid,
        page_count=temp_album.page_count,
        hash=temp_album.hash,
    )
    db.add(db_temp_album)
    db.commit()
    db.refresh(db_temp_album)
    return db_temp_album
