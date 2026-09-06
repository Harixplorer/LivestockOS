from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.schemas.animal import AnimalResponse
from app.schemas.alert import AlertResponse


class DashboardSummary(BaseModel):
    total_animals: int
    healthy_count: int
    warnings_count: int
    critical_count: int
    not_monitored_count: int
    sensors_online: int
    sensors_total: int
    average_health_score: Optional[float] = None


class QuickActionItem(BaseModel):
    id: str
    label: str
    route: str
    icon: Optional[str] = None


class ActivityItem(BaseModel):
    id: str
    title: str
    subtitle: str
    timestamp: datetime
    type: str


class DashboardResponse(BaseModel):
    farmer_name: str
    farm_name: str
    summary: DashboardSummary
    quick_actions: List[QuickActionItem]
    weekly_trend: List[Dict[str, Any]]
    animals_needing_attention: List[AnimalResponse]
    recent_activity: List[ActivityItem]
