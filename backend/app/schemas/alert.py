from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.alert import AlertSeverity


class AlertResponse(BaseModel):
    id: str
    farmer_id: str
    animal_id: str
    animal_name: Optional[str] = None
    tag_id: Optional[str] = None
    alert_type: str
    severity: AlertSeverity
    message: str
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertResolutionUpdate(BaseModel):
    is_resolved: bool


class AlertListResponse(BaseModel):
    total: int
    unresolved_count: int
    items: List[AlertResponse]
