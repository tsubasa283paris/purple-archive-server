from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import functions

from .database import Base


# ----------------------------------------------------------------
# definition of common columns as Mixin
# ----------------------------------------------------------------

# createdAt and updatedAt
class TimestampMixin(object):
    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(True),
            default=functions.now(),
            nullable=False
        )
    
    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(True),
            default=functions.now(),
            onupdate=functions.now(),
            nullable=False
        )
    

# ----------------------------------------------------------------
# definition of many-to-many intermediate tables
# ----------------------------------------------------------------

# Album-to-Tag
album_tag_table = Table(
    "album_tag",
    Base.metadata,
    Column(
        "album_id",
        ForeignKey("album.id"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("tag.id"),
        primary_key=True,
    ),
)

# User-to-Album
bookmark_table = Table(
    "bookmark",
    Base.metadata,
    Column(
        "user_id",
        ForeignKey("user.id"),
        primary_key=True,
    ),
    Column(
        "album_id",
        ForeignKey("album.id"),
        primary_key=True,
    ),
)


# ----------------------------------------------------------------
# definition of tables
# ----------------------------------------------------------------

class User(Base, TimestampMixin):
    __tablename__ = "user"

    id = Column(
        String(128),
        primary_key=True,
        index=True,
    )

    password = Column(
        String(128),
    )

    display_name = Column(
        String(256),
        index=True,
    )

    deleted_at = Column(
        DateTime(True),
        default=None,
        nullable=True,
    )

    bookmark_albums = relationship(
        "Album",
        secondary=bookmark_table,
        back_populates="bookmark_users",
    )


class Album(Base, TimestampMixin):
    __tablename__ = "album"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    source = Column(
        String(512),
    )

    thumb_source = Column(
        String(512),
    )

    hash = Column(
        String(512),
        index=True,
    )

    contributor_user_id = Column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )

    pv_count = Column(
        Integer,
        default=0,
    )

    download_count = Column(
        Integer,
        default=0,
    )

    gamemode_id = Column(
        ForeignKey("gamemode.id", ondelete="RESTRICT"),
    )

    played_at = Column(
        DateTime(True),
        nullable=True,
    )

    deleted_at = Column(
        DateTime(True),
        default=None,
        nullable=True,
    )

    gamemode = relationship("Gamemode", back_populates="albums")

    pages = relationship("Page", back_populates="album")

    bookmark_users = relationship(
        "User",
        secondary=bookmark_table,
        back_populates="bookmark_albums"
    )

    tags = relationship(
        "Tag",
        secondary=album_tag_table,
        back_populates="albums",
    )


class Page(Base, TimestampMixin):
    __tablename__ = "page"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    album_id = Column(
        ForeignKey("album.id", ondelete="CASCADE"),
    )

    index = Column(
        Integer,
    )

    description = Column(
        String(256),
    )

    player_name = Column(
        String(256),
    )

    album = relationship("Album", back_populates="pages")


class Gamemode(Base, TimestampMixin):
    __tablename__ = "gamemode"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    name = Column(
        String(256),
        unique=True,
    )

    albums = relationship("Album", back_populates="gamemode")


class Tag(Base, TimestampMixin):
    __tablename__ = "tag"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    name = Column(
        String(256),
        unique=True,
    )

    albums = relationship(
        "Album",
        secondary=album_tag_table,
        back_populates="tags",
    )


class TempAlbum(Base, TimestampMixin):
    __tablename__ = "temp_album"

    uuid = Column(
        String(128),
        primary_key=True,
        index=True,
    )

    page_count = Column(
        Integer,
    )

    hash = Column(
        String(128),
    )

    deleted_at = Column(
        DateTime(True),
        default=None,
        nullable=True,
    )
