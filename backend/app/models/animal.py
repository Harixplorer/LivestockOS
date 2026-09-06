import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class AnimalGender(str, enum.Enum):
    FEMALE = "FEMALE"
    MALE = "MALE"


class AnimalHealthStatus(str, enum.Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    NOT_MONITORED = "NOT_MONITORED"


class AnimalSensorStatus(str, enum.Enum):
    NOT_PAIRED = "NOT_PAIRED"
    PAIRED = "PAIRED"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class Animal(Base):
    __tablename__ = "animals"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    farmer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    tag_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    breed: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    age_months: Mapped[int] = mapped_column(Integer, nullable=True)
    gender: Mapped[AnimalGender] = mapped_column(
        SAEnum(AnimalGender, native_enum=False),
        default=AnimalGender.FEMALE,
        nullable=False
    )
    weight: Mapped[float] = mapped_column(Float, default=300.0, nullable=False)
    status: Mapped[AnimalHealthStatus] = mapped_column(
        SAEnum(AnimalHealthStatus, native_enum=False),
        default=AnimalHealthStatus.NOT_MONITORED,
        nullable=False
    )
    sensor_status: Mapped[AnimalSensorStatus] = mapped_column(
        SAEnum(AnimalSensorStatus, native_enum=False),
        default=AnimalSensorStatus.NOT_PAIRED,
        nullable=False
    )
    paired_sensor_id: Mapped[str] = mapped_column(String(50), nullable=True)
    paired_sensor_name: Mapped[str] = mapped_column(String(100), nullable=True)
    sensor_paired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    qr_code_payload: Mapped[str] = mapped_column(String(255), nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    farmer = relationship("User", back_populates="animals")
    readings = relationship("SensorReading", back_populates="animal", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="animal", cascade="all, delete-orphan")
    health_scores = relationship("HealthScore", back_populates="animal", cascade="all, delete-orphan")
