from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.camera import Camera


class CameraHealth(Base, UUIDMixin):
    __tablename__ = "camera_health"

    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    packet_loss_pct: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    current_fps: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    bitrate_kbps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    health_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    # Relationships
    camera: Mapped["Camera"] = relationship("Camera", back_populates="health_logs")
