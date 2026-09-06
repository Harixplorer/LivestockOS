from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.sensor import SensorCreate, SensorResponse
from app.services import sensor_service

router = APIRouter(prefix="/sensors", tags=["Sensors & Hardware"])


@router.get("", response_model=List[SensorResponse], summary="List all sensors")
async def list_sensors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await sensor_service.list_sensors(db)


@router.get("/available", response_model=List[SensorResponse], summary="List available unassigned sensors")
async def list_available_sensors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await sensor_service.list_available_sensors(db)


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new sensor device"
)
async def register_sensor(
    data: SensorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await sensor_service.create_sensor(db, data)
