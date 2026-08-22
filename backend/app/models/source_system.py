from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.camera import Camera


class SourceSystem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "source_systems"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(100), default="EXTERNAL_PROVIDED_CCTV_SOURCE", nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False, index=True)
    auth_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    cameras: Mapped[List["Camera"]] = relationship(
        "Camera", back_populates="source_system", lazy="selectin"
    )
