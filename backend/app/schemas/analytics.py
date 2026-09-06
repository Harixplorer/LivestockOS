from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class AnalyticsSummaryResponse(BaseModel):
    total_animals: int
    average_health_score: float
    sensors_online: int
    active_alerts: int
    animals_needing_attention: int


class HealthDistributionResponse(BaseModel):
    total: int
    healthy: int
    warning: int
    critical: int
    pending: int


class SensorCoverageResponse(BaseModel):
    total_animals: int
    paired: int
    not_paired: int
    online: int
    offline: int


class TrendPoint(BaseModel):
    timestamp: datetime
    avg_temperature: float
    avg_activity: int
    avg_rumination: int


class AnimalComparisonItem(BaseModel):
    animal_id: str
    name: str
    tag_id: str
    breed: str
    health_score: Optional[int] = None
    status: str
    temperature: Optional[float] = None
    activity: Optional[int] = None
    rumination: Optional[int] = None
