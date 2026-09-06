import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class HealthScore(Base):
    __tablename__ = "health_scores"

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
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    temp_component: Mapped[int] = mapped_column(Integer, default=35, nullable=False)
    activity_component: Mapped[int] = mapped_column(Integer, default=35, nullable=False)
    rumination_component: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    alert_penalty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False
    )

    animal = relationship("Animal", back_populates="health_scores")
