from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from app.core.enum.enum_classes import Status

class FurnaceBase(SQLModel):
    name: str = Field(index=True, nullable=False)
    status: Status = Field(index=True, default=Status.IDLE)    

class Furnace(FurnaceBase, table=True):
    __tablename__ = "furnaces"
    id :int = Field(primary_key=True, index=True)
    user_id : int | None = Field(default=None, foreign_key="users.id")
    user : Optional["User"] = Relationship(back_populates="furnaces") # pyright: ignore[reportUndefinedVariable]

    fabric_boiling_sessions: List["FabricBoilingSession"] = Relationship(back_populates="furnace") # pyright: ignore[reportUndefinedVariable]

class FurnacePublic(FurnaceBase):
    id:int

class FurnaceCreate(FurnaceBase):
    name: str

class FurnaceUpdate(FurnaceBase):
    name: Optional[str]=None
    status:Optional[str]=None