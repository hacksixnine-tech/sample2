from typing import TYPE_CHECKING, List, Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.analytics import Detection
    from app.models.watchlist import WatchlistEntry
    from app.models.user import User
    from app.models.alert import Alert


class Match(Base, UUIDMixin):
    __tablename__ = "matches"

    detection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("detections.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    watchlist_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("watchlist_entries.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    match_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    matching_method: Mapped[str] = mapped_column(String(50), default="EXACT_PLATE", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    verified_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    detection: Mapped["Detection"] = relationship("Detection", lazy="selectin")
    watchlist_entry: Mapped["WatchlistEntry"] = relationship("WatchlistEntry", back_populates="matches", lazy="selectin")
    verified_by: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="source_match", lazy="noload")
