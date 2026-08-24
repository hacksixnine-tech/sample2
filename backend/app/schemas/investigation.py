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
    speed_label: str = "ESTIMATED AVERAGE SPEED"
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
    sighting_id: Optional[uuid.UUID] = None
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
    
    # Forensic Transition Telemetry (Demarcated as Estimates)
    transition_distance_meters: Optional[float] = None
    transition_time_seconds: Optional[float] = None
    estimated_speed_kmph: Optional[float] = None
    speed_label: str = "ESTIMATED AVERAGE SPEED"
    anomaly_flag: Optional[str] = None
    matched_watchlist: bool = False
    watchlist_type: Optional[str] = None
    alert_id: Optional[uuid.UUID] = None
    incident_id: Optional[uuid.UUID] = None


class VehicleMovementHistory(BaseModel):
    vehicle_id: uuid.UUID
    normalized_plate: str
    raw_plate: str
    vehicle_type: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    sighting_count: int
    unique_camera_count: int
    unique_district_count: int
    sort_order: str = "desc"  # 'desc' (newest first for timeline) or 'asc' (oldest first for forward route)
    sightings: List[SightingDetail]


class VehicleSummaryResponse(BaseModel):
    vehicle_id: uuid.UUID
    normalized_plate: str
    raw_plate: str
    vehicle_type: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    owner_name: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    total_sightings: int = 0
    unique_cameras: int = 0
    unique_districts: int = 0
    watchlist_matches_count: int = 0
    alerts_count: int = 0
    watchlist_status: str = "CLEAR"  # 'CLEAR' | 'MATCH'
    highest_risk_level: Optional[str] = None
    investigation_status: str = "OPEN"  # 'OPEN' | 'UNDER_REVIEW' | 'WATCH' | 'RESOLVED' | 'ARCHIVED'
    average_transition_speed_kmph: Optional[float] = None
    speed_disclaimer: str = "ESTIMATED AVERAGE SPEED BETWEEN CAMERAS"
    is_demo: bool = False


class InvestigationNoteCreate(BaseModel):
    note: str = Field(..., min_length=1, max_length=5000)
    category: Optional[str] = Field("OBSERVATION", max_length=50)


class InvestigationNoteResponse(BaseModel):
    id: uuid.UUID
    investigation_id: uuid.UUID
    author_user_id: Optional[uuid.UUID] = None
    author_name: Optional[str] = None
    note: str
    category: str
    created_at: datetime


class InvestigationStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(OPEN|UNDER_REVIEW|WATCH|RESOLVED|ARCHIVED)$")
    reason: Optional[str] = None


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
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
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


# --- Master Prompt 09: Digital Forensics & Forensic Reporting Schemas ---

class EvidenceVerificationResponse(BaseModel):
    evidence_id: uuid.UUID
    status: str = Field(..., description="'INTEGRITY_VERIFIED' | 'INTEGRITY_CHECK_FAILED'")
    sha256_hash: Optional[str] = None
    expected_hash: Optional[str] = None
    algorithm: str = "SHA-256"
    verified_at: datetime
    message: str


class DetectionClassificationRequest(BaseModel):
    classification: str = Field(
        ..., pattern="^(CONFIRMED|FALSE_POSITIVE|NEEDS_REVIEW)$", description="Investigator classification"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Investigator classification rationale")


class DetectionClassificationResponse(BaseModel):
    detection_id: uuid.UUID
    classification: str
    notes: Optional[str] = None
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: datetime
    message: str = "Detection review classification updated successfully"


class CameraInvestigationContext(BaseModel):
    camera_id: uuid.UUID
    camera_code: str
    camera_name: str
    district: Optional[str] = None
    city: Optional[str] = None
    latitude: float
    longitude: float
    status: str
    total_detections_recorded: int
    total_alerts_triggered: int
    recent_sightings: List[Dict[str, Any]] = Field(default_factory=list)
    active_alerts: List[Dict[str, Any]] = Field(default_factory=list)


class DistrictInvestigationContext(BaseModel):
    district: str
    total_cameras: int
    active_incidents_count: int
    recent_alerts_count: int
    total_sightings_recorded: int
    high_risk_watchlist_matches: int


class ForensicReportResponse(BaseModel):
    report_id: uuid.UUID
    title: str
    investigation_code: str
    generated_at: datetime
    generated_by_user_id: Optional[uuid.UUID] = None
    generated_by_username: Optional[str] = None
    search_criteria: Dict[str, Any] = Field(default_factory=dict)
    vehicle: VehicleSummaryResponse
    dossier: VehicleInvestigationDossier
    route: VehicleRouteResponse
    timeline: InvestigationTimelineResponse
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)
    investigator_notes: List[Dict[str, Any]] = Field(default_factory=list)
    audit_metadata: Dict[str, Any] = Field(default_factory=dict)
    sha256_report_checksum: str = Field(..., description="Cryptographic SHA-256 seal of the forensic report")
