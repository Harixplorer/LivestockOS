from fastapi import APIRouter
from app.api.routes import (
    alerts,
    analytics,
    animals,
    auth,
    dashboard,
    qr,
    readings,
    sensors,
    users,
)

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(animals.router)
api_router.include_router(sensors.router)
api_router.include_router(readings.router)
api_router.include_router(alerts.router)
api_router.include_router(dashboard.router)
api_router.include_router(analytics.router)
api_router.include_router(qr.router)

__all__ = ["api_router", "auth"]
