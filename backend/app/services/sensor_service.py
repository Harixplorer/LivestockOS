from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.sensor import Sensor
from app.schemas.sensor import SensorCreate, SensorResponse


async def list_sensors(db: AsyncSession) -> List[SensorResponse]:
    result = await db.execute(select(Sensor).order_by(Sensor.created_at.desc()))
    return [SensorResponse.model_validate(s) for s in result.scalars().all()]


async def list_available_sensors(db: AsyncSession) -> List[SensorResponse]:
    result = await db.execute(
        select(Sensor)
        .where(Sensor.paired_animal_id == None, Sensor.is_active == True)
        .order_by(Sensor.sensor_id.asc())
    )
    return [SensorResponse.model_validate(s) for s in result.scalars().all()]


async def create_sensor(db: AsyncSession, data: SensorCreate) -> SensorResponse:
    existing = await db.execute(select(Sensor).where(Sensor.sensor_id == data.sensor_id))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sensor with ID '{data.sensor_id}' already registered."
        )

    sensor = Sensor(
        sensor_id=data.sensor_id,
        name=data.name,
        mac_address=data.mac_address,
        battery_level=data.battery_level,
        is_active=True
    )
    db.add(sensor)
    await db.commit()
    await db.refresh(sensor)
    return SensorResponse.model_validate(sensor)
