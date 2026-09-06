from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.alert import AlertListResponse, AlertResponse
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List herd alerts with optional filtering"
)
async def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, WARNING, INFO)"),
    is_resolved: Optional[bool] = Query(None, description="Filter by resolved state (true/false)"),
    search: Optional[str] = Query(None, description="Search by animal name, tag, or message"),
    sort: Optional[str] = Query(None, description="Sort: 'animalName', 'severity', 'date'"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items, total, unresolved = await alert_service.list_alerts(
        db=db,
        farmer_id=current_user.id,
        severity_filter=severity,
        is_resolved=is_resolved,
        search=search,
        sort_by=sort
    )
    return AlertListResponse(
        total=total,
        unresolved_count=unresolved,
        items=items
    )


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Get alert detail by ID"
)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await alert_service.get_alert(db, current_user.id, alert_id)


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
    summary="Mark an alert as resolved"
)
async def resolve_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await alert_service.set_alert_resolution(
        db=db,
        farmer_id=current_user.id,
        alert_id=alert_id,
        is_resolved=True
    )


@router.post(
    "/{alert_id}/reopen",
    response_model=AlertResponse,
    summary="Reopen an alert"
)
async def reopen_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await alert_service.set_alert_resolution(
        db=db,
        farmer_id=current_user.id,
        alert_id=alert_id,
        is_resolved=False
    )
