import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Union

from sqlalchemy import text, func
from sqlalchemy.orm import Session

from . import models, schemas


def remove_item_with_id(l: List, target_id: Any) -> List:
    for i, item in enumerate(l):
        if item.id == target_id:
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


@dataclass
class GetUsers:
    users: List[models.User]
    users_count: int


def get_users(db: Session, offset: int = 0, limit: int = 100):
    query = db.query(models.User) \
                .filter(models.User.deleted_at == None)
    total_count = query.count()
    return GetUsers(
        db.query(models.User) \
            .filter(models.User.deleted_at == None) \
            .offset(offset) \
            .limit(limit) \
            .all(),
        total_count
    )


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

GET_ALBUMS_ORDER_BY_PAT = 0 # order by playedAt
GET_ALBUMS_ORDER_BY_PVC = 1 # order by pvCount
GET_ALBUMS_ORDER_BY_DLC = 2 # order by downloadCount
GET_ALBUMS_ORDER_BY_BMC = 3 # order by bookmarkCount
GET_ALBUMS_ORDER_BY_PGC = 4 # order by pageCount

GET_ALBUMS_ORDER_ASC = 0 # order ascending
GET_ALBUMS_ORDER_DESC = 1 # order descending

@dataclass
class GetAlbums:
    albums: List[models.Album]
    albums_count: int

def get_albums(
    db: Session
):
    db_albums = db.query(models.Album) \
        .filter(models.Album.deleted_at == None) \
        .all()
    return GetAlbums(db_albums, len(db_albums))

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
            db_album.tags = remove_item_with_id(db_album.tags, db_tag.id)
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

def get_gamemode_by_name(db: Session, name: str):
    return db.query(models.Gamemode) \
        .filter(models.Gamemode.name == name) \
        .first()

@dataclass
class GetGamemodes:
    gamemodes: List[models.Gamemode]
    gamemodes_count: int

def get_gamemodes(
    db: Session, partial_name: str, offset: int = 0, limit: int = 100
):
    query = db.query(models.Gamemode)
    if len(partial_name):
        query = query.filter(
            models.Gamemode.name.like("%" + partial_name + "%")
        )
    total_count = query.count()
    return GetGamemodes(
        query \
            .offset(offset) \
            .limit(limit) \
            .all(),
        total_count
    )

def create_gamemode(db: Session, name: str):
    db_gamemode = models.Gamemode(
        name=name,
    )
    db.add(db_gamemode)
    db.commit()
    return db_gamemode

def delete_gamemode(db: Session, gamemode_id: int):
    db.query(models.Gamemode) \
        .filter(models.Gamemode.id == gamemode_id) \
        .delete()
    
    db.commit()


# ----------------------------------------------------------------
# tag
# ----------------------------------------------------------------

def get_tag(db: Session, id: int):
    return db.query(models.Tag) \
        .filter(models.Tag.id == id) \
        .first()

def get_tag_by_name(db: Session, name: str):
    return db.query(models.Tag) \
        .filter(models.Tag.name == name) \
        .first()

@dataclass
class GetTags:
    tags: List[models.Tag]
    tags_count: int

def get_tags(
    db: Session, partial_name: str, offset: int = 0, limit: int = 100
):
    query = db.query(models.Tag)
    if len(partial_name):
        query = query.filter(
            models.Tag.name.like("%" + partial_name + "%")
        )
    total_count = query.count()
    return GetTags(
        query \
            .offset(offset) \
            .limit(limit) \
            .all(),
        total_count
    )

def create_tag(db: Session, name: str):
    db_tag = models.Tag(
        name=name,
    )
    db.add(db_tag)
    db.commit()
    return db_tag

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


# ----------------------------------------------------------------
# bookmark
# ----------------------------------------------------------------

def add_bookmarks(db: Session, user_id: int, album_ids: List[int]):
    db_user = db.query(models.User) \
        .filter(models.User.id == user_id) \
        .first()
    assert db_user is not None

    # update user-album relations
    already_bookmarked_album_ids: Dict[int, bool] = {}
    bookmarked_album_ids: List[int] = []
    for bookmark_album in db_user.bookmark_albums:
        already_bookmarked_album_ids[bookmark_album.id] = True
        bookmarked_album_ids.append(bookmark_album.id)
    for album_id in album_ids:
        if already_bookmarked_album_ids.get(album_id):
            continue
        db_album = db.query(models.Album) \
            .filter(models.Album.id == album_id) \
            .first()
        if db_album is None:
            continue
        # add relation
        db_user.bookmark_albums.append(db_album)
        bookmarked_album_ids.append(db_album.id)
    
    db.commit()
    db.refresh(db_user)
    
    return bookmarked_album_ids

def remove_bookmarks(db: Session, user_id: int, album_ids: List[int]):
    db_user = db.query(models.User) \
        .filter(models.User.id == user_id) \
        .first()
    assert db_user is not None

    # update user-album relations
    already_bookmarked_album_ids: Dict[int, bool] = {}
    bookmarked_album_ids: List[int] = []
    for bookmark_album in db_user.bookmark_albums:
        already_bookmarked_album_ids[bookmark_album.id] = True
        bookmarked_album_ids.append(bookmark_album.id)
    for album_id in album_ids:
        if already_bookmarked_album_ids.get(album_id) is None:
            continue
        # remove relation
        db_user.bookmark_albums = remove_item_with_id(
            db_user.bookmark_albums, album_id
        )
        bookmarked_album_ids.remove(album_id)
    
    db.commit()
    db.refresh(db_user)
    
    return bookmarked_album_ids
