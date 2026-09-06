from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.reading import (
    SensorReadingCreate,
    SensorReadingDetail,
    SensorReadingResponse,
)
from app.services import telemetry_service

router = APIRouter(prefix="/readings", tags=["Readings & Telemetry"])


@router.post(
    "",
    response_model=SensorReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a sensor reading"
)
async def submit_reading(
    data: SensorReadingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await telemetry_service.ingest_reading(db, current_user.id, data)


@router.get(
    "/{animal_id}",
    response_model=List[SensorReadingDetail],
    summary="Get reading history for an animal"
)
async def get_animal_reading_history(
    animal_id: str,
    limit: int = Query(50, ge=1, le=500),
    period: Optional[str] = Query(None, description="'today', 'last7Days', or 'all'"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await telemetry_service.get_animal_readings(
        db=db,
        farmer_id=current_user.id,
        animal_id=animal_id,
        limit=limit,
        period=period
    )
