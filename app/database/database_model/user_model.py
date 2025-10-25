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
    created_at: datetime = Field(index=True, default=datetime.now())
    esps : List["ESP"]= Relationship(back_populates="user")

class UserPublic(UserBase):
    id: int

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: str
