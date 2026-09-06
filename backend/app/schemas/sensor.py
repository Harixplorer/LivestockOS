from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SensorBase(BaseModel):
    sensor_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(default="LivestockOS_Sensor", max_length=100)
    mac_address: Optional[str] = None
    battery_level: int = Field(default=100, ge=0, le=100)


class SensorCreate(SensorBase):
    pass


class SensorResponse(SensorBase):
    id: str
    is_active: bool
    paired_animal_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SensorPairRequest(BaseModel):
    sensor_id: str = Field(..., min_length=1, max_length=50)
    sensor_name: Optional[str] = "LivestockOS_Sensor"
