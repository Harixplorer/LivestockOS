from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import case, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.animal import (
    Animal,
    AnimalGender,
    AnimalHealthStatus,
    AnimalSensorStatus,
)
from app.models.health_score import HealthScore
from app.models.reading import SensorReading
from app.models.sensor import Sensor
from app.schemas.animal import (
    AnimalCreate,
    AnimalResponse,
    AnimalUpdate,
    HerdStatsResponse,
)


def _generate_qr_payload(animal_id: str, tag_id: str, name: str) -> str:
    """Encode QR payload matching frontend AnimalQrPayload format."""
    now_str = datetime.now(timezone.utc).isoformat()
    return f"LIVESTOCKOS|{animal_id}|{tag_id}|{name}|{now_str}"


async def attach_vitals(db: AsyncSession, animal: Animal) -> AnimalResponse:
    """Attach the latest telemetry and health score to animal response."""
    resp = AnimalResponse.model_validate(animal)

    # Only load vitals if monitored / paired
    if animal.status != AnimalHealthStatus.NOT_MONITORED:
        # Latest reading
        reading_q = await db.execute(
            select(SensorReading)
            .where(SensorReading.animal_id == animal.id)
            .order_by(SensorReading.recorded_at.desc())
            .limit(1)
        )
        latest_reading = reading_q.scalars().first()
        if latest_reading:
            resp.temperature = latest_reading.temperature
            resp.activity_level = latest_reading.activity_score
            resp.rumination = latest_reading.rumination_mins

        # Latest health score
        score_q = await db.execute(
            select(HealthScore)
            .where(HealthScore.animal_id == animal.id)
            .order_by(HealthScore.calculated_at.desc())
            .limit(1)
        )
        latest_score = score_q.scalars().first()
        if latest_score:
            resp.health_score = latest_score.score

    return resp


async def create_animal(
    db: AsyncSession,
    farmer_id: str,
    data: AnimalCreate
) -> AnimalResponse:
    """Create a new animal record scoped to the authenticated farmer."""
    # Check tag uniqueness for this farmer
    existing_tag = await db.execute(
        select(Animal).where(
            Animal.farmer_id == farmer_id,
            Animal.tag_id == data.tag_id.strip()
        )
    )
    if existing_tag.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An animal with Tag ID '{data.tag_id}' already exists in your herd."
        )

    animal = Animal(
        farmer_id=farmer_id,
        tag_id=data.tag_id.strip(),
        name=data.name.strip(),
        breed=data.breed.strip(),
        age=data.age,
        age_months=data.age_months or (data.age * 12),
        gender=data.gender,
        weight=data.weight,
        status=AnimalHealthStatus.NOT_MONITORED,
        sensor_status=AnimalSensorStatus.NOT_PAIRED,
    )
    db.add(animal)
    await db.flush()

    # Generate QR payload
    animal.qr_code_payload = _generate_qr_payload(animal.id, animal.tag_id, animal.name)
    await db.commit()
    await db.refresh(animal)

    return await attach_vitals(db, animal)


async def get_animal(
    db: AsyncSession,
    farmer_id: str,
    animal_id: str
) -> AnimalResponse:
    """Get single animal by ID with ownership verification."""
    result = await db.execute(
        select(Animal).where(Animal.id == animal_id, Animal.farmer_id == farmer_id)
    )
    animal = result.scalars().first()
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal with ID '{animal_id}' not found."
        )
    return await attach_vitals(db, animal)


async def list_animals(
    db: AsyncSession,
    farmer_id: str,
    search: Optional[str] = None,
    breed: Optional[str] = None,
    status_filter: Optional[str] = None,
    sort_by: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> Tuple[List[AnimalResponse], int]:
    """List animals with search, filtering, and sorting."""
    query = select(Animal).where(Animal.farmer_id == farmer_id)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(Animal.name).like(search_term),
                func.lower(Animal.tag_id).like(search_term),
                func.lower(Animal.breed).like(search_term),
            )
        )

    if breed:
        query = query.where(func.lower(Animal.breed) == breed.lower().strip())

    if status_filter:
        status_norm = status_filter.upper().strip()
        if status_norm == "PENDING":
            query = query.where(Animal.status == AnimalHealthStatus.NOT_MONITORED)
        elif status_norm in AnimalHealthStatus.__members__:
            query = query.where(Animal.status == AnimalHealthStatus[status_norm])

    # Sorting
    if sort_by == "gender":
        # Females first, then by name alphabetically
        gender_order = case(
            (Animal.gender == AnimalGender.FEMALE, 0),
            else_=1
        )
        query = query.order_by(gender_order, Animal.name.asc())
    elif sort_by == "name":
        query = query.order_by(Animal.name.asc())
    elif sort_by == "tag":
        query = query.order_by(Animal.tag_id.asc())
    else:
        query = query.order_by(Animal.created_at.desc())

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    animals = result.scalars().all()

    items = [await attach_vitals(db, a) for a in animals]
    return items, total


async def update_animal(
    db: AsyncSession,
    farmer_id: str,
    animal_id: str,
    data: AnimalUpdate
) -> AnimalResponse:
    """Update editable animal details."""
    result = await db.execute(
        select(Animal).where(Animal.id == animal_id, Animal.farmer_id == farmer_id)
    )
    animal = result.scalars().first()
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal with ID '{animal_id}' not found."
        )

    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(animal, field, value)

    # Re-generate QR payload if tag or name changes
    if "tag_id" in update_dict or "name" in update_dict:
        animal.qr_code_payload = _generate_qr_payload(animal.id, animal.tag_id, animal.name)

    await db.commit()
    await db.refresh(animal)
    return await attach_vitals(db, animal)


async def delete_animal(
    db: AsyncSession,
    farmer_id: str,
    animal_id: str
) -> None:
    """Delete animal and unpair associated sensors."""
    result = await db.execute(
        select(Animal).where(Animal.id == animal_id, Animal.farmer_id == farmer_id)
    )
    animal = result.scalars().first()
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal with ID '{animal_id}' not found."
        )

    # Release any paired sensor
    if animal.paired_sensor_id:
        sensor_res = await db.execute(
            select(Sensor).where(Sensor.sensor_id == animal.paired_sensor_id)
        )
        sensor = sensor_res.scalars().first()
        if sensor:
            sensor.paired_animal_id = None

    await db.delete(animal)
    await db.commit()


async def pair_sensor(
    db: AsyncSession,
    farmer_id: str,
    animal_id: str,
    sensor_id_str: str,
    sensor_name: Optional[str] = "LivestockOS_Sensor"
) -> AnimalResponse:
    """Pair a hardware sensor to an animal."""
    result = await db.execute(
        select(Animal).where(Animal.id == animal_id, Animal.farmer_id == farmer_id)
    )
    animal = result.scalars().first()
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal with ID '{animal_id}' not found."
        )

    # Check if sensor exists or register it
    sensor_res = await db.execute(
        select(Sensor).where(Sensor.sensor_id == sensor_id_str)
    )
    sensor = sensor_res.scalars().first()
    if not sensor:
        sensor = Sensor(
            sensor_id=sensor_id_str,
            name=sensor_name or "LivestockOS_Sensor",
            battery_level=100,
            is_active=True
        )
        db.add(sensor)
        await db.flush()

    # Check if already paired to another animal
    if sensor.paired_animal_id and sensor.paired_animal_id != animal_id:
        other_q = await db.execute(
            select(Animal).where(Animal.id == sensor.paired_animal_id)
        )
        other = other_q.scalars().first()
        other_name = other.name if other else sensor.paired_animal_id
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sensor '{sensor_id_str}' is already paired to {other_name}."
        )

    sensor.paired_animal_id = animal.id
    animal.paired_sensor_id = sensor.sensor_id
    animal.paired_sensor_name = sensor.name
    animal.sensor_status = AnimalSensorStatus.ONLINE
    animal.sensor_paired_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(animal)
    return await attach_vitals(db, animal)


async def unpair_sensor(
    db: AsyncSession,
    farmer_id: str,
    animal_id: str
) -> AnimalResponse:
    """Unpair sensor from animal without deleting historical readings."""
    result = await db.execute(
        select(Animal).where(Animal.id == animal_id, Animal.farmer_id == farmer_id)
    )
    animal = result.scalars().first()
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal with ID '{animal_id}' not found."
        )

    if animal.paired_sensor_id:
        sensor_res = await db.execute(
            select(Sensor).where(Sensor.sensor_id == animal.paired_sensor_id)
        )
        sensor = sensor_res.scalars().first()
        if sensor:
            sensor.paired_animal_id = None

    animal.paired_sensor_id = None
    animal.paired_sensor_name = None
    animal.sensor_status = AnimalSensorStatus.NOT_PAIRED
    animal.sensor_paired_at = None

    await db.commit()
    await db.refresh(animal)
    return await attach_vitals(db, animal)


async def compute_herd_stats(
    db: AsyncSession,
    farmer_id: str
) -> HerdStatsResponse:
    """Compute aggregate herd health statistics."""
    result = await db.execute(
        select(Animal).where(Animal.farmer_id == farmer_id)
    )
    animals = result.scalars().all()

    total = len(animals)
    healthy = sum(1 for a in animals if a.status == AnimalHealthStatus.HEALTHY)
    warnings = sum(1 for a in animals if a.status == AnimalHealthStatus.WARNING)
    critical = sum(1 for a in animals if a.status == AnimalHealthStatus.CRITICAL)
    not_monitored = sum(1 for a in animals if a.status == AnimalHealthStatus.NOT_MONITORED)
    sensors_online = sum(1 for a in animals if a.sensor_status == AnimalSensorStatus.ONLINE)

    # Average health score of monitored animals
    scores_query = await db.execute(
        select(func.avg(HealthScore.score))
        .join(Animal, HealthScore.animal_id == Animal.id)
        .where(Animal.farmer_id == farmer_id)
    )
    avg_score = scores_query.scalar()

    return HerdStatsResponse(
        total=total,
        healthy_count=healthy,
        warnings_count=warnings,
        critical_count=critical,
        not_monitored_count=not_monitored,
        sensors_online=sensors_online,
        sensors_total=total,
        average_health_score=round(float(avg_score), 1) if avg_score else None
    )
