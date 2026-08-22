from typing import TYPE_CHECKING, List, Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.user import User
    from app.models.alert import Alert
    from app.models.analytics import Event, Entity, Evidence


class IncidentAlert(Base):
    __tablename__ = "incident_alerts"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), primary_key=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="alerts", lazy="selectin")
    alert: Mapped["Alert"] = relationship("Alert", back_populates="incident_links", lazy="selectin")


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="events", lazy="selectin")
    event: Mapped["Event"] = relationship("Event", lazy="selectin")


class IncidentEntity(Base):
    __tablename__ = "incident_entities"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True
    )
    involvement_role: Mapped[str] = mapped_column(
        String(50), primary_key=True, default="SUSPECT", nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="entities", lazy="selectin")
    entity: Mapped["Entity"] = relationship("Entity", lazy="selectin")


class IncidentEvidence(Base):
    __tablename__ = "incident_evidence"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="evidence_links", lazy="selectin")
    evidence: Mapped["Evidence"] = relationship("Evidence", lazy="selectin")


class Incident(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "incidents"

    incident_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="OPEN", nullable=False, index=True)
    assigned_department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    assigned_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closing_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    assigned_department: Mapped[Optional["Department"]] = relationship("Department", lazy="selectin")
    assigned_user: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    
    alerts: Mapped[List["IncidentAlert"]] = relationship(
        "IncidentAlert", back_populates="incident", cascade="all, delete-orphan", lazy="selectin"
    )
    events: Mapped[List["IncidentEvent"]] = relationship(
        "IncidentEvent", back_populates="incident", cascade="all, delete-orphan", lazy="selectin"
    )
    entities: Mapped[List["IncidentEntity"]] = relationship(
        "IncidentEntity", back_populates="incident", cascade="all, delete-orphan", lazy="selectin"
    )
    evidence_links: Mapped[List["IncidentEvidence"]] = relationship(
        "IncidentEvidence", back_populates="incident", cascade="all, delete-orphan", lazy="selectin"
    )
