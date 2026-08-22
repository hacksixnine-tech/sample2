from typing import TYPE_CHECKING, List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Boolean, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.camera import Camera
    from app.models.location import Location


class Entity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "entities"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    primary_identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_sightings: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    vehicle: Mapped[Optional["Vehicle"]] = relationship(
        "Vehicle", back_populates="entity", uselist=False, lazy="selectin"
    )


class Vehicle(Base, TimestampMixin):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    normalized_plate: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    raw_plate: Mapped[str] = mapped_column(String(50), nullable=False)
    plate_state_code: Mapped[Optional[str]] = mapped_column(String(10), default="GJ")
    vehicle_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    make: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    chassis_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    engine_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    owner_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rto_registered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    entity: Mapped["Entity"] = relationship("Entity", back_populates="vehicle", lazy="selectin")
    observations: Mapped[List["VehicleObservation"]] = relationship(
        "VehicleObservation", back_populates="vehicle", lazy="noload"
    )


class Detection(Base, UUIDMixin):
    __tablename__ = "detections"

    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    detection_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    bounding_box: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    detected_plate_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    normalized_plate_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    frame_reference: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    crop_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    speed_estimate_kmph: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    direction_heading: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    object_class: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    inference_event_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    source_camera_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_system_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    inference_time_ms: Mapped[Optional[float]] = mapped_column(Numeric(12, 3), nullable=True)
    device: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anpr_claimed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evidence_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    camera: Mapped["Camera"] = relationship("Camera", lazy="selectin")


class Event(Base, UUIDMixin):
    __tablename__ = "events"

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="RESTRICT"), nullable=False
    )
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="SET NULL"), nullable=True
    )
    detection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("detections.id", ondelete="SET NULL"), nullable=True
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="INFO", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    processed_by_worker: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Evidence(Base, UUIDMixin):
    __tablename__ = "evidence"

    evidence_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(50), default="LOCAL_STORAGE", nullable=False)
    bucket_name: Mapped[str] = mapped_column(String(100), default="phantom-evidence", nullable=False)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_format: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    file_hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="RESTRICT"), nullable=False
    )
    detection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("detections.id", ondelete="SET NULL"), nullable=True
    )
    event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    chain_of_custody_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hash_algorithm: Mapped[str] = mapped_column(String(32), default="SHA-256", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    retention_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    public_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)


class VehicleObservation(Base, UUIDMixin):
    __tablename__ = "vehicle_observations"

    vehicle_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    detection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("detections.id", ondelete="SET NULL"), nullable=True
    )
    evidence_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    raw_plate: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    normalized_plate: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    plate_confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    vehicle_confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    frame_reference: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    detection_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    observation_identity: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    inference_event_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anpr_claimed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle", back_populates="observations", lazy="selectin")
    camera: Mapped["Camera"] = relationship("Camera", lazy="selectin")
    location: Mapped[Optional["Location"]] = relationship("Location", lazy="selectin")


class AIIngestEvent(Base, UUIDMixin):
    __tablename__ = "ai_ingest_events"

    inference_event_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    camera_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    payload_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    result_summary: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
