import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    animal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("animals.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    activity_score: Mapped[int] = mapped_column(Integer, nullable=False)
    behavior: Mapped[str] = mapped_column(String(50), default="Idle", nullable=False)
    rumination_mins: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False
    )

    animal = relationship("Animal", back_populates="readings")
