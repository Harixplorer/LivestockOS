from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    AnimalComparisonItem,
    HealthDistributionResponse,
    SensorCoverageResponse,
    TrendPoint,
)
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics & Health Intelligence"])


@router.get("/summary", response_model=AnalyticsSummaryResponse, summary="Get herd analytics overview")
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await analytics_service.get_analytics_summary(db, current_user.id)


@router.get("/distribution", response_model=HealthDistributionResponse, summary="Get health score distribution")
async def get_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await analytics_service.get_health_distribution(db, current_user.id)


@router.get("/sensors", response_model=SensorCoverageResponse, summary="Get sensor coverage breakdown")
async def get_sensor_coverage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await analytics_service.get_sensor_coverage(db, current_user.id)


@router.get("/trends", response_model=List[TrendPoint], summary="Get 24-hour herd vital trends")
async def get_trends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await analytics_service.get_herd_trends(db, current_user.id)


@router.get("/comparison", response_model=List[AnimalComparisonItem], summary="Get animal comparison matrix")
async def get_comparison(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await analytics_service.get_animal_comparison(db, current_user.id)
