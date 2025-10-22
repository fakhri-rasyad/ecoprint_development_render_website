from datetime import datetime
from sqlmodel import SQLModel, Field

class SensorReading(SQLModel):
    __tablename__ = "sensor_readings"

    id : int= Field(primary_key=True, index=True)
    timestamp: datetime = Field(index=True, default=datetime.utcnow)
    temperature: float = Field(index=True)
    humidity: float = Field(index=True)
    color_r :int= Field(index=True)
    color_g : int= Field(index=True)
    color_b: int = Field(index=True)

    # esp_id = Field(Integer, ForeignKey("esps.id"))
    # batch_id = Field(Integer, ForeignKey("fabric_batches.id"))

    # esp = relationship("ESP", back_populates="readings")
    # batch = relationship("FabricBatch", back_populates="readings")
