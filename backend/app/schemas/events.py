from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class EventType(str, Enum):
    # Camera Events
    CAMERA_ONLINE = "CAMERA_ONLINE"
    CAMERA_OFFLINE = "CAMERA_OFFLINE"
    CAMERA_STREAM_DEGRADED = "CAMERA_STREAM_DEGRADED"

    # AI & ANPR Detection Events
    VEHICLE_DETECTED = "VEHICLE_DETECTED"
    ANPR_DETECTED = "ANPR_DETECTED"
    WATCHLIST_MATCH = "WATCHLIST_MATCH"

    # Alert Lifecycle Events
    ALERT_CREATED = "ALERT_CREATED"
    ALERT_UPDATED = "ALERT_UPDATED"
    ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED"
    ALERT_RESOLVED = "ALERT_RESOLVED"
    ALERT_DISMISSED = "ALERT_DISMISSED"

    # Vehicle Tracking Events
    VEHICLE_SIGHTING = "VEHICLE_SIGHTING"
    VEHICLE_ROUTE_UPDATED = "VEHICLE_ROUTE_UPDATED"

    # System Health Events
    SYSTEM_HEALTH_CHANGED = "SYSTEM_HEALTH_CHANGED"
    AI_SERVICE_STATUS_CHANGED = "AI_SERVICE_STATUS_CHANGED"


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "phantom-event-bus"
    camera_id: Optional[str] = None
    district: Optional[str] = None
    severity: Optional[str] = None  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    entity_type: Optional[str] = None  # vehicle, camera, system, alert
    entity_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventSubscription(BaseModel):
    categories: List[str] = Field(default_factory=lambda: ["*"])  # ALERTS, ANPR, CAMERAS, HEALTH, VEHICLES, or *
    district: Optional[str] = None
    min_severity: Optional[str] = None


class HistoricalEventsResponse(BaseModel):
    total_events: int
    since_timestamp: Optional[str] = None
    events: List[EventEnvelope]
