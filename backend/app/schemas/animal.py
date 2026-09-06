from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.animal import (
    AnimalGender,
    AnimalHealthStatus,
    AnimalSensorStatus,
)


class AnimalBase(BaseModel):
    tag_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    breed: str = Field(..., min_length=1, max_length=100)
    age: int = Field(default=1, ge=0, description="Age in years")
    age_months: Optional[int] = Field(default=None, ge=0)
    gender: AnimalGender = AnimalGender.FEMALE
    weight: float = Field(default=300.0, gt=0)


class AnimalCreate(AnimalBase):
    pass


class AnimalUpdate(BaseModel):
    name: Optional[str] = None
    tag_id: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None
    age_months: Optional[int] = None
    gender: Optional[AnimalGender] = None
    weight: Optional[float] = None
    status: Optional[AnimalHealthStatus] = None


class AnimalResponse(AnimalBase):
    id: str
    farmer_id: str
    status: AnimalHealthStatus
    sensor_status: AnimalSensorStatus
    paired_sensor_id: Optional[str] = None
    paired_sensor_name: Optional[str] = None
    sensor_paired_at: Optional[datetime] = None
    qr_code_payload: Optional[str] = None
    last_updated: Optional[datetime] = None
    created_at: datetime

    # Computed/latest vitals (null if no sensor or not monitored)
    health_score: Optional[int] = None
    temperature: Optional[float] = None
    activity_level: Optional[int] = None
    rumination: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class AnimalListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[AnimalResponse]


class HerdStatsResponse(BaseModel):
    total: int
    healthy_count: int
    warnings_count: int
    critical_count: int
    not_monitored_count: int
    sensors_online: int
    sensors_total: int
    average_health_score: Optional[float] = None
