from typing import TYPE_CHECKING, List, Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.user import User
    from app.models.match import Match


class Watchlist(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "watchlists"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    department: Mapped["Department"] = relationship("Department", lazy="selectin")
    created_by: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    entries: Mapped[List["WatchlistEntry"]] = relationship(
        "WatchlistEntry", back_populates="watchlist", cascade="all, delete-orphan", lazy="selectin"
    )


class WatchlistEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "watchlist_entries"

    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), default="VEHICLE", nullable=False, index=True)
    case_reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fir_station: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False)
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    watchlist: Mapped["Watchlist"] = relationship("Watchlist", back_populates="entries", lazy="selectin")
    matches: Mapped[List["Match"]] = relationship("Match", back_populates="watchlist_entry", lazy="noload")
