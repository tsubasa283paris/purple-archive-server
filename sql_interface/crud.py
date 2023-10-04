import datetime
from typing import Any, Dict, List, Union

from sqlalchemy.orm import Session

from . import models, schemas


def remove_item_with_id(l: List, target: Any) -> List:
    for i, item in enumerate(l):
        if item.id == target.id:
            return l[:i] + l[i + 1:]
    raise ValueError("target not in list")


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

def get_album(db: Session, id: int, pv_increment: bool = False):
    db_album = db.query(models.Album) \
        .filter(
            models.Album.id == id,
            models.Album.deleted_at == None
        ) \
        .first()
    if pv_increment and db_album is not None:
        db_album.pv_count += 1
        db.commit()
    return db_album

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

def update_album(
    db: Session, id: int, gamemode_id: int,
    tag_ids: List[int], page_meta_data: List[schemas.PageMetaData]
):
    db_album = db.query(models.Album) \
        .filter(
            models.Album.id == id,
            models.Album.deleted_at == None
        ) \
        .first()
    
    # update gamemode_id
    db_album.gamemode_id = gamemode_id
    
    # update album-tag relations
    already_related_tag_ids: Dict[int, bool] = {}
    for tag in db_album.tags:
        already_related_tag_ids[tag.id] = True
    # when already related tag was not specified
    for already_related_tag_id in already_related_tag_ids.keys():
        if not already_related_tag_id in tag_ids:
            db_tag = get_tag(db, already_related_tag_id)
            db_album.tags = remove_item_with_id(db_album.tags, db_tag)
            # delete tag if no album is related
            if len(db_tag.albums) == 0:
                db.query(models.Tag) \
                    .filter(models.Tag.id == db_tag.id) \
                    .delete()
    # when specified tags that are not related now
    for tag_id in tag_ids:
        if already_related_tag_ids.get(tag_id):
            continue

        db_tag = get_tag(db, tag_id)
        db_album.tags.append(db_tag)
    
    # update page records
    for i, page in enumerate(page_meta_data):
        db_page = db.query(models.Page) \
            .filter(
                models.Page.album_id == db_album.id,
                models.Page.index == i
            ) \
            .first()
        assert db_page is not None
        db_page.description = page.description
        db_page.player_name = page.player_name
    
    db.commit()
    db.refresh(db_album)

    return db_album

def soft_delete_album(
    db: Session, id: int
):
    db_album = db.query(models.Album) \
        .filter(models.Album.id == id) \
        .first()
    db_album.deleted_at = datetime.datetime.now().astimezone()

    db.commit()

def increment_album_dlcount(
    db: Session, id: int
):
    db_album = db.query(models.Album) \
        .filter(models.Album.id == id) \
        .first()
    db_album.download_count += 1

    db.commit()

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
