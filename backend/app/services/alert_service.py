from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.alert import Alert, AlertSeverity
from app.models.animal import Animal
from app.schemas.alert import AlertResponse


async def list_alerts(
    db: AsyncSession,
    farmer_id: str,
    severity_filter: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
) -> Tuple[List[AlertResponse], int, int]:
    """List alerts for farmer's herd with filtering and search."""
    query = (
        select(Alert, Animal.name.label("animal_name"), Animal.tag_id.label("tag_id"))
        .join(Animal, Alert.animal_id == Animal.id)
        .where(Alert.farmer_id == farmer_id)
    )

    if severity_filter:
        sev_norm = severity_filter.upper().strip()
        if sev_norm in AlertSeverity.__members__:
            query = query.where(Alert.severity == AlertSeverity[sev_norm])

    if is_resolved is not None:
        query = query.where(Alert.is_resolved == is_resolved)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(Animal.name).like(search_term),
                func.lower(Animal.tag_id).like(search_term),
                func.lower(Alert.message).like(search_term),
                func.lower(Alert.alert_type).like(search_term),
            )
        )

    if sort_by == "animalName":
        query = query.order_by(Animal.name.asc())
    elif sort_by == "severity":
        query = query.order_by(Alert.severity.asc())
    else:
        query = query.order_by(Alert.created_at.desc())

    result = await db.execute(query)
    rows = result.all()

    items = []
    for alert, animal_name, tag_id in rows:
        resp = AlertResponse(
            id=alert.id,
            farmer_id=alert.farmer_id,
            animal_id=alert.animal_id,
            animal_name=animal_name,
            tag_id=tag_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            message=alert.message,
            is_resolved=alert.is_resolved,
            resolved_at=alert.resolved_at,
            created_at=alert.created_at,
        )
        items.append(resp)

    # Counts
    total = len(items)
    unresolved_count = sum(1 for item in items if not item.is_resolved)

    return items, total, unresolved_count


async def get_alert(
    db: AsyncSession,
    farmer_id: str,
    alert_id: str
) -> AlertResponse:
    """Fetch single alert by ID with ownership verification."""
    query = (
        select(Alert, Animal.name.label("animal_name"), Animal.tag_id.label("tag_id"))
        .join(Animal, Alert.animal_id == Animal.id)
        .where(Alert.id == alert_id, Alert.farmer_id == farmer_id)
    )
    result = await db.execute(query)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID '{alert_id}' not found."
        )

    alert, animal_name, tag_id = row
    return AlertResponse(
        id=alert.id,
        farmer_id=alert.farmer_id,
        animal_id=alert.animal_id,
        animal_name=animal_name,
        tag_id=tag_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        message=alert.message,
        is_resolved=alert.is_resolved,
        resolved_at=alert.resolved_at,
        created_at=alert.created_at,
    )


async def set_alert_resolution(
    db: AsyncSession,
    farmer_id: str,
    alert_id: str,
    is_resolved: bool
) -> AlertResponse:
    """Resolve or reopen an alert."""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.farmer_id == farmer_id)
    )
    alert = result.scalars().first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID '{alert_id}' not found."
        )

    alert.is_resolved = is_resolved
    alert.resolved_at = datetime.now(timezone.utc) if is_resolved else None

    await db.commit()
    await db.refresh(alert)
    return await get_alert(db, farmer_id, alert_id)
