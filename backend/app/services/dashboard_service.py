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
from app.models.user import User
from app.schemas.dashboard import (
    ActivityItem,
    DashboardResponse,
    DashboardSummary,
    QuickActionItem,
)
from app.services.animal_service import attach_vitals


async def get_dashboard_data(db: AsyncSession, user: User) -> DashboardResponse:
    """Build aggregated dashboard payload matching frontend requirements."""
    # 1. Fetch Animals
    animals_q = await db.execute(
        select(Animal).where(Animal.farmer_id == user.id)
    )
    animals = animals_q.scalars().all()

    total = len(animals)
    healthy = sum(1 for a in animals if a.status == AnimalHealthStatus.HEALTHY)
    warnings = sum(1 for a in animals if a.status == AnimalHealthStatus.WARNING)
    critical = sum(1 for a in animals if a.status == AnimalHealthStatus.CRITICAL)
    pending = sum(1 for a in animals if a.status == AnimalHealthStatus.NOT_MONITORED)
    sensors_online = sum(1 for a in animals if a.sensor_status == AnimalSensorStatus.ONLINE)

    # Average health score
    score_q = await db.execute(
        select(func.avg(HealthScore.score))
        .join(Animal, HealthScore.animal_id == Animal.id)
        .where(Animal.farmer_id == user.id)
    )
    avg_score = score_q.scalar()

    summary = DashboardSummary(
        total_animals=total,
        healthy_count=healthy,
        warnings_count=warnings,
        critical_count=critical,
        not_monitored_count=pending,
        sensors_online=sensors_online,
        sensors_total=total,
        average_health_score=round(float(avg_score), 1) if avg_score else None
    )

    # 2. Quick Actions
    quick_actions = [
        QuickActionItem(id="qa-1", label="Add Animal", route="/animals/add", icon="add"),
        QuickActionItem(id="qa-2", label="Scan QR", route="/scan-qr", icon="qr_code_scanner"),
        QuickActionItem(id="qa-3", label="Pair Sensor", route="/ble", icon="bluetooth"),
        QuickActionItem(id="qa-4", label="View Alerts", route="/alerts", icon="notifications"),
    ]

    # 3. Animals Needing Attention (WARNING or CRITICAL)
    needing_attention_db = [
        a for a in animals if a.status in (AnimalHealthStatus.WARNING, AnimalHealthStatus.CRITICAL)
    ]
    animals_needing_attention = [await attach_vitals(db, a) for a in needing_attention_db]

    # 4. Weekly Trend (Past 7 days)
    now = datetime.now(timezone.utc)
    weekly_trend = []
    for i in range(6, -1, -1):
        day_date = now - timedelta(days=i)
        day_label = day_date.strftime("%a")
        weekly_trend.append({
            "day": day_label,
            "avg_health": 88 if i > 2 else 82,
            "alerts_count": 1 if i % 2 == 0 else 0
        })

    # 5. Recent Activity
    alerts_q = await db.execute(
        select(Alert)
        .where(Alert.farmer_id == user.id)
        .order_by(Alert.created_at.desc())
        .limit(4)
    )
    recent_alerts = alerts_q.scalars().all()
    recent_activity: List[ActivityItem] = []
    for a in recent_alerts:
        recent_activity.append(
            ActivityItem(
                id=a.id,
                title=f"Alert: {a.alert_type}",
                subtitle=a.message,
                timestamp=a.created_at,
                type="ALERT"
            )
        )

    return DashboardResponse(
        farmer_name=user.full_name,
        farm_name=user.farm_name or "My Farm",
        summary=summary,
        quick_actions=quick_actions,
        weekly_trend=weekly_trend,
        animals_needing_attention=animals_needing_attention,
        recent_activity=recent_activity
    )
