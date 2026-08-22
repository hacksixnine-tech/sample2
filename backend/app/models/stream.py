from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.camera import Camera


class CameraStream(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "camera_streams"

    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    protocol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    stream_url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resolution: Mapped[str] = mapped_column(String(50), default="1080p", nullable=False)
    fps: Mapped[float] = mapped_column(Numeric(5, 2), default=25.0, nullable=False)
    codec: Mapped[str] = mapped_column(String(50), default="H264", nullable=False)
    bitrate_kbps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    # Relationships
    camera: Mapped["Camera"] = relationship("Camera", back_populates="streams")
