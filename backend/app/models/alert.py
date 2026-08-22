from typing import TYPE_CHECKING, List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.camera import Camera
    from app.models.analytics import Entity, Event
    from app.models.match import Match
    from app.models.user import User
    from app.models.incident import IncidentAlert


class Alert(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "alerts"

    alert_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="NEW", nullable=False, index=True)
    source_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    source_match_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="SET NULL"), nullable=True
    )
    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    acknowledged_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    camera: Mapped["Camera"] = relationship("Camera", lazy="selectin")
    entity: Mapped[Optional["Entity"]] = relationship("Entity", lazy="selectin")
    source_event: Mapped[Optional["Event"]] = relationship("Event", lazy="selectin")
    source_match: Mapped[Optional["Match"]] = relationship("Match", back_populates="alerts", lazy="selectin")
    acknowledged_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[acknowledged_by_user_id], lazy="selectin")
    resolved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[resolved_by_user_id], lazy="selectin")
    incident_links: Mapped[List["IncidentAlert"]] = relationship("IncidentAlert", back_populates="alert", cascade="all, delete-orphan", lazy="noload")
