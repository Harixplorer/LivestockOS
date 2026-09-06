from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SensorReadingCreate(BaseModel):
    animal_id: str
    temperature: float = Field(..., ge=30.0, le=45.0, description="Temperature in Celsius")
    activity_score: int = Field(..., ge=0, le=100, description="Activity index 0-100")
    behavior: str = Field(default="Idle", max_length=50)
    rumination_mins: Optional[int] = Field(default=20, ge=0, le=60, description="Minutes/hr")
    timestamp: Optional[datetime] = None


class SensorReadingResponse(BaseModel):
    reading_id: str
    alert_generated: bool
    alert_type: Optional[str] = None
    health_score: int
    anomaly_score: float


class SensorReadingDetail(BaseModel):
    id: str
    animal_id: str
    temperature: float
    activity_score: int
    behavior: str
    rumination_mins: int
    is_anomaly: bool
    anomaly_score: float
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)
