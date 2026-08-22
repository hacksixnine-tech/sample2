from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class RoutePoint(BaseModel):
    sequence: int
    camera_id: uuid.UUID
    camera_name: Optional[str] = None
    source_camera_id: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    latitude: float
    longitude: float
    timestamp: datetime
    straight_line_distance_prev_meters: Optional[float] = None
    time_delta_prev_seconds: Optional[float] = None
    geographic_speed_kmph: Optional[float] = None
    anomaly_flag: Optional[str] = None


class VehicleRouteResponse(BaseModel):
    vehicle_id: uuid.UUID
    normalized_plate: str
    route_type: str = "OBSERVED_CAMERA_SEQUENCE"  # Explicitly distinguished from INFERRED/ESTIMATED road routing
    point_count: int
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    total_geographic_distance_meters: float = 0.0
    unique_camera_count: int = 0
    unique_district_count: int = 0
    points: List[RoutePoint]
    anomalies_detected: List[Dict[str, Any]] = Field(default_factory=list)


class SightingDetail(BaseModel):
    camera_id: uuid.UUID
    camera_name: Optional[str] = None
    source_camera_id: Optional[str] = None
    district: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: datetime
    plate_confidence: Optional[float] = None
    vehicle_confidence: Optional[float] = None
    evidence_reference: Optional[str] = None
    alert_reference: Optional[str] = None
    frame_reference: Optional[str] = None
    is_demo: bool = False


class VehicleMovementHistory(BaseModel):
    vehicle_id: uuid.UUID
    normalized_plate: str
    raw_plate: str
    vehicle_type: Optional[str] = None
    first_seen: datetime
    last_seen: datetime
    sighting_count: int
    unique_camera_count: int
    unique_district_count: int
    sightings: List[SightingDetail]


class InvestigationTimelineEvent(BaseModel):
    timestamp: datetime
    event_type: str  # DETECTION, ANPR, OBSERVATION, WATCHLIST_MATCH, ALERT, INCIDENT
    camera_id: Optional[uuid.UUID] = None
    camera_name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confidence: Optional[float] = None
    reference_id: Optional[str] = None
    severity: Optional[str] = None
    title: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InvestigationTimelineResponse(BaseModel):
    vehicle_id: uuid.UUID
    normalized_plate: str
    total_events: int
    first_event_at: Optional[datetime] = None
    last_event_at: Optional[datetime] = None
    events: List[InvestigationTimelineEvent]


class InvestigationSearchResult(BaseModel):
    query: Dict[str, Any]
    total_vehicles: int
    total_observations: int
    total_alerts: int
    total_incidents: int
    vehicles: List[Dict[str, Any]] = Field(default_factory=list)
    observations: List[Dict[str, Any]] = Field(default_factory=list)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    incidents: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)


class VehicleInvestigationDossier(BaseModel):
    identity: str
    vehicle_id: uuid.UUID
    plate: str
    raw_plate: str
    vehicle_type: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    owner_name: Optional[str] = None
    first_seen: datetime
    last_seen: datetime
    sighting_count: int
    camera_count: int
    district_count: int
    districts_visited: List[str] = Field(default_factory=list)
    cameras_visited: List[str] = Field(default_factory=list)
    observations: List[Dict[str, Any]] = Field(default_factory=list)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    watchlist_matches: List[Dict[str, Any]] = Field(default_factory=list)
    incidents: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    anomalies: List[Dict[str, Any]] = Field(default_factory=list)
