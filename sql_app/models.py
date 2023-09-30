import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from .database import Base


class TimestampMixin(object):
    @declared_attr
    def created_at(cls):
        return Column(
            DateTime,
            default=datetime.datetime.now(),
            nullable=False
        )
    
    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=datetime.datetime.now(),
            onupdate=datetime.datetime.now(),
            nullable=False
        )


class User(Base, TimestampMixin):
    __tablename__ = "user"

    id = Column(
        String,
        primary_key=True,
        index=True,
    )

    password = Column(
        String,
    )

    display_name = Column(
        String,
        index=True,
    )

    items = relationship("Item", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, index=True)

    description = Column(String, index=True)

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    owner = relationship("User", back_populates="items")
