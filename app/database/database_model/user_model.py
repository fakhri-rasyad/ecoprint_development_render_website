from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import List
from zoneinfo import ZoneInfo

class UserBase(SQLModel):
    username: str = Field(index=True, nullable=False)
    email: str = Field(index=True, unique=True)

class User(UserBase, table=True):
    __tablename__ = "users"
    id: int = Field(primary_key=True, index=True)
    password_hash: str = Field(index=True, nullable=False)
    created_at: datetime = Field(index=True, default=datetime.now(ZoneInfo("Asia/Makassar")))

    esps : List["ESP"]= Relationship(back_populates="user") # pyright: ignore[reportUndefinedVariable]
    furnaces:List["Furnace"] = Relationship(back_populates="user") # pyright: ignore[reportUndefinedVariable]

class UserPublic(UserBase):
    id: int

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: str
