from app.schemas.common import ErrorResponse, MessageResponse
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    TokenPayload,
)
from app.schemas.user import UserResponse, UserCreate, UserUpdate
from app.schemas.animal import (
    AnimalCreate,
    AnimalUpdate,
    AnimalResponse,
    AnimalListResponse,
    HerdStatsResponse,
)
from app.schemas.sensor import (
    SensorCreate,
    SensorResponse,
    SensorPairRequest,
)
from app.schemas.reading import (
    SensorReadingCreate,
    SensorReadingResponse,
    SensorReadingDetail,
)
from app.schemas.alert import (
    AlertResponse,
    AlertResolutionUpdate,
    AlertListResponse,
)
from app.schemas.dashboard import DashboardResponse, DashboardSummary
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    HealthDistributionResponse,
    SensorCoverageResponse,
    TrendPoint,
    AnimalComparisonItem,
)
from app.schemas.qr import QrLookupResponse

__all__ = [
    "ErrorResponse",
    "MessageResponse",
    "RegisterRequest",
    "LoginRequest",
    "RefreshRequest",
    "TokenResponse",
    "TokenPayload",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    "AnimalCreate",
    "AnimalUpdate",
    "AnimalResponse",
    "AnimalListResponse",
    "HerdStatsResponse",
    "SensorCreate",
    "SensorResponse",
    "SensorPairRequest",
    "SensorReadingCreate",
    "SensorReadingResponse",
    "SensorReadingDetail",
    "AlertResponse",
    "AlertResolutionUpdate",
    "AlertListResponse",
    "DashboardResponse",
    "DashboardSummary",
    "AnalyticsSummaryResponse",
    "HealthDistributionResponse",
    "SensorCoverageResponse",
    "TrendPoint",
    "AnimalComparisonItem",
    "QrLookupResponse",
]
