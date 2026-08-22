from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.department import Department
from app.models.location import Location
from app.models.camera import Camera
from app.models.stream import CameraStream
from app.models.health import CameraHealth
from app.models.audit import AuditLog
from app.models.source_system import SourceSystem
from app.models.user import Role, User
from app.models.watchlist import Watchlist, WatchlistEntry
from app.models.match import Match
from app.models.alert import Alert
from app.models.incident import (
    Incident,
    IncidentAlert,
    IncidentEvent,
    IncidentEntity,
    IncidentEvidence,
)
from app.models.analytics import (
    Entity,
    Vehicle,
    Detection,
    Event,
    Evidence,
    VehicleObservation,
    AIIngestEvent,
)

__all__ = [
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    "Department",
    "Location",
    "Camera",
    "CameraStream",
    "CameraHealth",
    "AuditLog",
    "SourceSystem",
    "Role",
    "User",
    "Watchlist",
    "WatchlistEntry",
    "Match",
    "Alert",
    "Incident",
    "IncidentAlert",
    "IncidentEvent",
    "IncidentEntity",
    "IncidentEvidence",
    "Entity",
    "Vehicle",
    "Detection",
    "Event",
    "Evidence",
    "VehicleObservation",
    "AIIngestEvent",
]
