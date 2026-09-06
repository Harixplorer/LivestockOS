from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.alert import Alert, AlertSeverity
from app.models.animal import Animal, AnimalHealthStatus
from app.models.health_score import HealthScore
from app.models.reading import SensorReading
from app.schemas.reading import (
    SensorReadingCreate,
    SensorReadingDetail,
    SensorReadingResponse,
)


def evaluate_telemetry_rules(
    temperature: float,
    activity_score: int,
    rumination_mins: int
) -> Optional[Tuple[str, AlertSeverity, str]]:
    """Evaluate cattle vitals against veterinary threshold rules."""
    # 1. Temperature checks
    if temperature >= 40.5:
        return (
            "HIGH_FEVER",
            AlertSeverity.CRITICAL,
            f"Critical high fever ({temperature:.1f}°C) detected — immediate attention required."
        )
    elif temperature >= 39.5:
        return (
            "FEVER",
            AlertSeverity.WARNING,
            f"Elevated body temperature ({temperature:.1f}°C) detected — monitor closely."
        )
    elif temperature < 37.5:
        return (
            "HYPOTHERMIA",
            AlertSeverity.WARNING,
            f"Low body temperature ({temperature:.1f}°C) detected."
        )

    # 2. Rumination checks
    if rumination_mins < 10:
        return (
            "LOW_RUMINATION",
            AlertSeverity.WARNING,
            f"Abnormally low rumination ({rumination_mins} min/hr) detected."
        )

    # 3. Activity checks
    if activity_score < 15:
        return (
            "INACTIVITY",
            AlertSeverity.WARNING,
            f"Lethargy or prolonged inactivity detected (activity score {activity_score})."
        )

    return None


def calculate_health_score(
    temperature: float,
    activity_score: int,
    rumination_mins: int,
    active_alerts_count: int
) -> Tuple[int, int, int, int, int]:
    """Calculate composite cattle health score (0-100)."""
    # Temperature component (max 40 pts)
    temp_diff = abs(temperature - 38.6)
    if temp_diff <= 0.5:
        temp_comp = 40
    elif temp_diff <= 1.0:
        temp_comp = 30
    elif temp_diff <= 1.8:
        temp_comp = 15
    else:
        temp_comp = 5

    # Activity component (max 30 pts)
    if activity_score >= 50:
        act_comp = 30
    elif activity_score >= 30:
        act_comp = 20
    else:
        act_comp = 10

    # Rumination component (max 30 pts)
    if rumination_mins >= 20:
        rum_comp = 30
    elif rumination_mins >= 10:
        rum_comp = 18
    else:
        rum_comp = 5

    # Alert penalty
    penalty = min(active_alerts_count * 15, 40)

    total_score = max(0, min(100, (temp_comp + act_comp + rum_comp) - penalty))
    return total_score, temp_comp, act_comp, rum_comp, penalty


async def ingest_reading(
    db: AsyncSession,
    farmer_id: str,
    data: SensorReadingCreate
) -> SensorReadingResponse:
    """Ingest sensor reading, run rule checks, update health score and status."""
    result = await db.execute(
        select(Animal).where(Animal.id == data.animal_id, Animal.farmer_id == farmer_id)
    )
    animal = result.scalars().first()
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal with ID '{data.animal_id}' not found."
        )

    recorded_time = data.timestamp or datetime.now(timezone.utc)

    # 1. Rule Engine
    alert_info = evaluate_telemetry_rules(
        temperature=data.temperature,
        activity_score=data.activity_score,
        rumination_mins=data.rumination_mins or 0
    )

    alert_generated = False
    alert_type_str: Optional[str] = None

    if alert_info:
        alert_type_str, severity, message = alert_info
        alert_generated = True

        new_alert = Alert(
            farmer_id=farmer_id,
            animal_id=animal.id,
            alert_type=alert_type_str,
            severity=severity,
            message=message,
            is_resolved=False,
            created_at=recorded_time
        )
        db.add(new_alert)

    # 2. Anomaly score
    anomaly_score = -0.55 if alert_generated else 0.10
    is_anomaly = alert_generated

    # 3. Save Reading
    reading = SensorReading(
        animal_id=animal.id,
        temperature=data.temperature,
        activity_score=data.activity_score,
        behavior=data.behavior,
        rumination_mins=data.rumination_mins or 0,
        is_anomaly=is_anomaly,
        anomaly_score=anomaly_score,
        recorded_at=recorded_time
    )
    db.add(reading)

    # 4. Count active alerts
    alerts_q = await db.execute(
        select(Alert).where(Alert.animal_id == animal.id, Alert.is_resolved == False)
    )
    active_alerts = len(alerts_q.scalars().all())
    if alert_generated:
        active_alerts += 1

    # 5. Calculate composite health score
    score, temp_c, act_c, rum_c, penalty = calculate_health_score(
        temperature=data.temperature,
        activity_score=data.activity_score,
        rumination_mins=data.rumination_mins or 0,
        active_alerts_count=active_alerts
    )

    health_score_entry = HealthScore(
        animal_id=animal.id,
        score=score,
        temp_component=temp_c,
        activity_component=act_c,
        rumination_component=rum_c,
        alert_penalty=penalty,
        calculated_at=recorded_time
    )
    db.add(health_score_entry)

    # 6. Update Animal status
    animal.last_updated = recorded_time
    if score >= 75:
        animal.status = AnimalHealthStatus.HEALTHY
    elif score >= 50:
        animal.status = AnimalHealthStatus.WARNING
    else:
        animal.status = AnimalHealthStatus.CRITICAL

    await db.commit()
    await db.refresh(reading)

    return SensorReadingResponse(
        reading_id=reading.id,
        alert_generated=alert_generated,
        alert_type=alert_type_str,
        health_score=score,
        anomaly_score=anomaly_score
    )


async def get_animal_readings(
    db: AsyncSession,
    farmer_id: str,
    animal_id: str,
    limit: int = 50,
    period: Optional[str] = None
) -> List[SensorReadingDetail]:
    """Fetch readings for an animal with optional period filtering."""
    # Ensure ownership
    animal_check = await db.execute(
        select(Animal).where(Animal.id == animal_id, Animal.farmer_id == farmer_id)
    )
    if not animal_check.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal with ID '{animal_id}' not found."
        )

    query = select(SensorReading).where(SensorReading.animal_id == animal_id)

    if period == "today":
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.where(SensorReading.recorded_at >= today_start)
    elif period == "last7Days":
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        query = query.where(SensorReading.recorded_at >= seven_days_ago)

    query = query.order_by(SensorReading.recorded_at.desc()).limit(limit)
    result = await db.execute(query)
    readings = result.scalars().all()
    return [SensorReadingDetail.model_validate(r) for r in readings]
