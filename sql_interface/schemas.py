import datetime
from typing import List, Union

from pydantic import BaseModel
from pydantic.alias_generators import to_camel


# ----------------------------------------------------------------
# common fields
# ----------------------------------------------------------------

class CommonRead(BaseModel):
    created_at: datetime.datetime
    updated_at: datetime.datetime


# ----------------------------------------------------------------
# user
# ----------------------------------------------------------------

class UserBase(BaseModel):
    id: str
    display_name: str

    class Config:
        orm_mode = True


class UserRead(UserBase, CommonRead):
    pass


class UserReadDeep(UserRead):
    bookmark_albums: "List[AlbumRead]"


class UserWrite(UserBase):
    password: str

    class Config:
        alias_generator = to_camel


class UserUpdate(UserWrite):
    deleted_at: Union[datetime.datetime, None]


# ----------------------------------------------------------------
# album
# ----------------------------------------------------------------

class AlbumBase(BaseModel):
    source: str
    hash: str
    contributor_user_id: Union[str, None]
    pv_count: int
    download_count: int
    gamemode_id: int
    played_at: Union[datetime.datetime, None]
    deleted_at: Union[datetime.datetime, None]

    class Config:
        orm_mode = True


class AlbumRead(AlbumBase, CommonRead):
    id: int


class AlbumReadDeep(AlbumRead):
    gamemode: "GamemodeRead"
    pages: "List[PageRead]"
    bookmark_users: "List[UserRead]"
    tags: "List[TagRead]"


class AlbumWrite(AlbumBase):
    class Config:
        alias_generator = to_camel


# ----------------------------------------------------------------
# page
# ----------------------------------------------------------------

class PageBase(BaseModel):
    album_id: int
    index: int
    description: str
    player_name: str

    class Config:
        orm_mode = True


class PageRead(PageBase, CommonRead):
    id: int


class PageReadDeep(AlbumBase):
    album: "AlbumRead"


class PageWrite(PageBase):
    class Config:
        alias_generator = to_camel


# ----------------------------------------------------------------
# gamemode
# ----------------------------------------------------------------

class GamemodeBase(BaseModel):
    name: str

    class Config:
        orm_mode = True
    

class GamemodeRead(GamemodeBase, CommonRead):
    id: int


class GamemodeReadDeep(GamemodeRead):
    albums: "List[AlbumRead]"


class GamemodeWrite(GamemodeBase):
    class Config:
        alias_generator = to_camel


# ----------------------------------------------------------------
# tag
# ----------------------------------------------------------------

class TagBase(BaseModel):
    name: str

    class Config:
        orm_mode = True
    

class TagRead(TagBase, CommonRead):
    id: int


class TagReadDeep(TagRead):
    albums: "List[AlbumRead]"


class TagWrite(TagBase):
    class Config:
        alias_generator = to_camel


# ----------------------------------------------------------------
# temp_album
# ----------------------------------------------------------------

class TempAlbumBase(BaseModel):
    uuid: str
    page_count: int
    deleted_at: Union[datetime.datetime, None]


class TempAlbumRead(TempAlbumBase, CommonRead):
    pass


class TempAlbumReadDeep(TempAlbumRead):
    pass


class TempAlbumWrite(TempAlbumBase):
    class Config:
        alias_generator = to_camel


# ----------------------------------------------------------------
# update forward references
# ----------------------------------------------------------------
UserReadDeep.model_rebuild()
AlbumReadDeep.model_rebuild()
PageReadDeep.model_rebuild()
GamemodeReadDeep.model_rebuild()
TagReadDeep.model_rebuild()
