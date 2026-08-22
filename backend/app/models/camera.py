from typing import TYPE_CHECKING, List, Optional
from datetime import date, datetime
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.location import Location
    from app.models.stream import CameraStream
    from app.models.health import CameraHealth
    from app.models.source_system import SourceSystem


class Camera(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cameras"

    camera_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    camera_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    ownership: Mapped[str] = mapped_column(String(100), default="Gujarat Government", nullable=False)
    installation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False, index=True)
    connectivity_status: Mapped[str] = mapped_column(
        String(50), default="ONLINE", nullable=False, index=True
    )
    storage_type: Mapped[str] = mapped_column(String(50), default="EDGE_AND_CENTRAL", nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    field_of_view_deg: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    azimuth_angle_deg: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    # Source System Preservation Fields
    source_system_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_systems.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_camera_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    last_connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    department: Mapped["Department"] = relationship(
        "Department", back_populates="cameras", lazy="selectin"
    )
    location: Mapped["Location"] = relationship(
        "Location", back_populates="cameras", lazy="selectin"
    )
    streams: Mapped[List["CameraStream"]] = relationship(
        "CameraStream", back_populates="camera", lazy="selectin", cascade="all, delete-orphan"
    )
    health_logs: Mapped[List["CameraHealth"]] = relationship(
        "CameraHealth", back_populates="camera", lazy="selectin", cascade="all, delete-orphan"
    )
    source_system: Mapped[Optional["SourceSystem"]] = relationship(
        "SourceSystem", back_populates="cameras", lazy="selectin"
    )
