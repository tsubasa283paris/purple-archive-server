from typing import List, Union

from pydantic import BaseModel


class ItemBase(BaseModel):
    title: str
    description: Union[str, None] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    id: str
    password: str
    display_name: str


class UserCreate(UserBase):
    pass


class User(UserBase):
    items: List[Item] = []

    class Config:
        orm_mode = True
