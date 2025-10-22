from datetime import datetime
from sqlmodel import SQLModel, Field

class Furnace(SQLModel):
    __tablename__ = "furnaces"

    id = Field(primary_key=True, index=True)
    name = Field(index=True, nullable=False)
    status = Field(index=True, default="idle")

    # esps = relationship("ESP", back_populates="furnace")
    # batches = relationship("FabricBatch", back_populates="furnace")
