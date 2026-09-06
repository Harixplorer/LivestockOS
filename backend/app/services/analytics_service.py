from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.alert import Alert
from app.models.animal import (
    Animal,
    AnimalHealthStatus,
    AnimalSensorStatus,
)
from app.models.health_score import HealthScore
from app.models.reading import SensorReading
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    AnimalComparisonItem,
    HealthDistributionResponse,
    SensorCoverageResponse,
    TrendPoint,
)
from app.services.animal_service import attach_vitals


async def get_analytics_summary(db: AsyncSession, farmer_id: str) -> AnalyticsSummaryResponse:
    """Fetch analytics overview metrics."""
    animals_q = await db.execute(select(Animal).where(Animal.farmer_id == farmer_id))
    animals = animals_q.scalars().all()

    total = len(animals)
    sensors_online = sum(1 for a in animals if a.sensor_status == AnimalSensorStatus.ONLINE)
    attention = sum(1 for a in animals if a.status in (AnimalHealthStatus.WARNING, AnimalHealthStatus.CRITICAL))

    alerts_q = await db.execute(
        select(func.count()).where(Alert.farmer_id == farmer_id, Alert.is_resolved == False)
    )
    active_alerts = alerts_q.scalar_one()

    score_q = await db.execute(
        select(func.avg(HealthScore.score))
        .join(Animal, HealthScore.animal_id == Animal.id)
        .where(Animal.farmer_id == farmer_id)
    )
    avg_score = score_q.scalar()

    return AnalyticsSummaryResponse(
        total_animals=total,
        average_health_score=round(float(avg_score), 1) if avg_score else 0.0,
        sensors_online=sensors_online,
        active_alerts=active_alerts,
        animals_needing_attention=attention,
    )


async def get_health_distribution(db: AsyncSession, farmer_id: str) -> HealthDistributionResponse:
    """Calculate counts per health classification."""
    animals_q = await db.execute(select(Animal).where(Animal.farmer_id == farmer_id))
    animals = animals_q.scalars().all()

    total = len(animals)
    healthy = sum(1 for a in animals if a.status == AnimalHealthStatus.HEALTHY)
    warning = sum(1 for a in animals if a.status == AnimalHealthStatus.WARNING)
    critical = sum(1 for a in animals if a.status == AnimalHealthStatus.CRITICAL)
    pending = sum(1 for a in animals if a.status == AnimalHealthStatus.NOT_MONITORED)

    return HealthDistributionResponse(
        total=total,
        healthy=healthy,
        warning=warning,
        critical=critical,
        pending=pending,
    )


async def get_sensor_coverage(db: AsyncSession, farmer_id: str) -> SensorCoverageResponse:
    """Calculate sensor pairing and connectivity rates."""
    animals_q = await db.execute(select(Animal).where(Animal.farmer_id == farmer_id))
    animals = animals_q.scalars().all()

    total = len(animals)
    paired = sum(1 for a in animals if a.sensor_status in (AnimalSensorStatus.PAIRED, AnimalSensorStatus.ONLINE))
    not_paired = sum(1 for a in animals if a.sensor_status == AnimalSensorStatus.NOT_PAIRED)
    online = sum(1 for a in animals if a.sensor_status == AnimalSensorStatus.ONLINE)
    offline = sum(1 for a in animals if a.sensor_status == AnimalSensorStatus.OFFLINE)

    return SensorCoverageResponse(
        total_animals=total,
        paired=paired,
        not_paired=not_paired,
        online=online,
        offline=offline,
    )


async def get_herd_trends(db: AsyncSession, farmer_id: str) -> List[TrendPoint]:
    """Generate 24 hourly data points for herd vitals."""
    now = datetime.now(timezone.utc)
    points: List[TrendPoint] = []

    for hour_offset in range(23, -1, -1):
        point_time = now - timedelta(hours=hour_offset)
        # In production, query average vitals within window; provide realistic baseline
        points.append(
            TrendPoint(
                timestamp=point_time,
                avg_temperature=round(38.5 + (0.3 if hour_offset % 4 == 0 else -0.2), 2),
                avg_activity=65 + (5 if hour_offset % 3 == 0 else -5),
                avg_rumination=22 + (2 if hour_offset % 2 == 0 else -3),
            )
        )
    return points


async def get_animal_comparison(db: AsyncSession, farmer_id: str) -> List[AnimalComparisonItem]:
    """Provide comparison metrics across animals in the herd."""
    animals_q = await db.execute(select(Animal).where(Animal.farmer_id == farmer_id))
    animals = animals_q.scalars().all()

    items: List[AnimalComparisonItem] = []
    for a in animals:
        vital_animal = await attach_vitals(db, a)
        items.append(
            AnimalComparisonItem(
                animal_id=vital_animal.id,
                name=vital_animal.name,
                tag_id=vital_animal.tag_id,
                breed=vital_animal.breed,
                health_score=vital_animal.health_score,
                status=vital_animal.status.value,
                temperature=vital_animal.temperature,
                activity=vital_animal.activity_level,
                rumination=vital_animal.rumination,
            )
        )
    return items
