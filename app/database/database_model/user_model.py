from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import List

class UserBase(SQLModel):
    username: str = Field(index=True, nullable=False)
    email: str = Field(index=True, unique=True)

class User(UserBase, table=True):
    __tablename__ = "users"
    id: int = Field(primary_key=True, index=True)
    password_hash: str = Field(index=True, nullable=False)
    fcm_token:str = Field(index=True, nullable=True)
    created_at: datetime = Field(index=True, default_factory=datetime.now)

    esps : List["ESP"]= Relationship(back_populates="user") # pyright: ignore[reportUndefinedVariable]
    furnaces:List["Furnace"] = Relationship(back_populates="user") # pyright: ignore[reportUndefinedVariable]

class UserPublic(UserBase):
    id: int

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: str
