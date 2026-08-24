from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.ai.anpr.normalize import normalize_plate_text
from app.ai.postprocessing.classes import normalize_detection_class
from app.ai.postprocessing.validation import parse_bbox, validate_confidence


class BoundingBoxSchema(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

    @model_validator(mode="after")
    def check_order(self):
        parse_bbox({"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2})
        return self


class PlatePayload(BaseModel):
    raw: str = Field(..., min_length=1, max_length=50)
    normalized: Optional[str] = Field(None, max_length=50)
    confidence: float

    @field_validator("confidence")
    @classmethod
    def conf(cls, v: float) -> float:
        return validate_confidence(v, "plate.confidence")

    @field_validator("raw")
    @classmethod
    def strip_raw(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def fill_normalized(self):
        if not self.normalized:
            self.normalized = normalize_plate_text(self.raw)
        else:
            self.normalized = normalize_plate_text(self.normalized)
        return self


class ModelInfo(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., min_length=1, max_length=50)


class DetectionIngestItem(BaseModel):
    type: str = Field(..., description="Model or PHANTOM class name")
    confidence: float
    bbox: Union[List[float], Dict[str, float], BoundingBoxSchema]
    plate: Optional[PlatePayload] = None
    plate_bbox: Optional[Union[List[float], Dict[str, float]]] = None
    plate_crop_reference: Optional[str] = Field(None, max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    detection_id: Optional[str] = Field(None, max_length=64)

    @field_validator("confidence")
    @classmethod
    def conf(cls, v: float) -> float:
        return validate_confidence(v)

    @field_validator("type")
    @classmethod
    def ntype(cls, v: str) -> str:
        return normalize_detection_class(v)

    @field_validator("bbox")
    @classmethod
    def vbbox(cls, v):
        box = parse_bbox(v if not isinstance(v, BoundingBoxSchema) else v.model_dump())
        return box.as_dict()

    @field_validator("metadata")
    @classmethod
    def cap_meta(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if v is None:
            return {}
        encoded = str(v)
        if len(encoded) > 8000:
            raise ValueError("metadata exceeds size limit")
        return v


class DetectionCreate(BaseModel):
    camera_id: uuid.UUID
    timestamp: datetime
    type: str
    confidence: float
    bbox: Union[List[float], Dict[str, float]]
    plate: Optional[PlatePayload] = None
    frame_reference: Optional[str] = Field(None, max_length=500)
    model_name: Optional[str] = Field(None, max_length=100)
    model_version: Optional[str] = Field(None, max_length=50)
    inference_event_id: Optional[str] = Field(None, max_length=128)
    source_camera_id: Optional[str] = Field(None, max_length=100)
    is_demo: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence")
    @classmethod
    def conf(cls, v: float) -> float:
        return validate_confidence(v)

    @field_validator("type")
    @classmethod
    def ntype(cls, v: str) -> str:
        return normalize_detection_class(v)

    @field_validator("bbox")
    @classmethod
    def vbbox(cls, v):
        return parse_bbox(v).as_dict()

    @field_validator("timestamp")
    @classmethod
    def ts(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class DetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    camera_id: uuid.UUID
    entity_id: Optional[uuid.UUID] = None
    detection_type: str
    object_class: Optional[str] = None
    detected_at: datetime
    confidence: float
    bounding_box: Dict[str, Any]
    detected_plate_number: Optional[str] = None
    normalized_plate_number: Optional[str] = None
    frame_reference: Optional[str] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    inference_event_id: Optional[str] = None
    inference_time_ms: Optional[float] = None
    device: Optional[str] = None
    is_demo: bool = False
    anpr_claimed: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")

    @field_validator("confidence", "inference_time_ms", mode="before")
    @classmethod
    def num(cls, v):
        return float(v) if v is not None else v


class AIResultIngestRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "inference_event_id": "demo-evt-0001",
                    "camera_id": "50000000-0000-0000-0000-000000000001",
                    "source_camera_id": "SRC-DEMO-001",
                    "timestamp": "2026-08-22T05:00:00Z",
                    "model": {"name": "phantom-demo-detector", "version": "demo-1.0.0"},
                    "frame_reference": "demo://sample-frame",
                    "is_demo": True,
                    "detections": [
                        {
                            "type": "LICENSE_PLATE",
                            "confidence": 0.95,
                            "bbox": [100, 200, 300, 260],
                            "plate": {
                                "raw": "GJ 01 TEST 001",
                                "normalized": "GJ01TEST001",
                                "confidence": 0.94,
                            },
                        }
                    ],
                }
            ]
        }
    )

    camera_id: uuid.UUID
    timestamp: datetime
    model: ModelInfo
    detections: List[DetectionIngestItem]
    frame_reference: Optional[str] = Field(None, max_length=500)
    source_camera_id: Optional[str] = Field(None, max_length=100)
    source_system_id: Optional[uuid.UUID] = None
    inference_event_id: Optional[str] = Field(None, max_length=128)
    inference_time_ms: Optional[float] = Field(None, ge=0)
    device: Optional[str] = Field(None, max_length=20)
    is_demo: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def ts(cls, v: datetime) -> datetime:
        if v.year < 2000 or v.year > 2100:
            raise ValueError("timestamp out of acceptable range")
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @field_validator("detections")
    @classmethod
    def caps(cls, v: List[DetectionIngestItem]) -> List[DetectionIngestItem]:
        if not v:
            raise ValueError("detections must not be empty")
        from app.core.config import settings

        if len(v) > settings.AI_INGEST_MAX_DETECTIONS:
            raise ValueError("too many detections in a single payload")
        return v


class AIResultIngestResponse(BaseModel):
    inference_event_id: str
    idempotent_replay: bool = False
    is_demo: bool = False
    detections_created: int = 0
    observations_created: int = 0
    observations_deduplicated: int = 0
    vehicles_created: int = 0
    events_created: int = 0
    evidence_ids: List[uuid.UUID] = Field(default_factory=list)
    detection_ids: List[uuid.UUID] = Field(default_factory=list)
    vehicle_ids: List[uuid.UUID] = Field(default_factory=list)


class ANPRObservationCreate(BaseModel):
    camera_id: uuid.UUID
    timestamp: datetime
    raw_plate: str = Field(..., min_length=1, max_length=50)
    normalized_plate: Optional[str] = None
    plate_confidence: float
    vehicle_confidence: Optional[float] = None
    frame_reference: Optional[str] = Field(None, max_length=500)
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    inference_event_id: Optional[str] = None
    is_demo: bool = False
    bbox: Optional[Union[List[float], Dict[str, float]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("plate_confidence", "vehicle_confidence")
    @classmethod
    def conf(cls, v):
        if v is None:
            return v
        return validate_confidence(v)

    @field_validator("timestamp")
    @classmethod
    def ts(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode="after")
    def norm(self):
        self.normalized_plate = normalize_plate_text(self.normalized_plate or self.raw_plate)
        return self


class ANPRObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    vehicle_id: Optional[uuid.UUID] = None
    camera_id: uuid.UUID
    location_id: Optional[uuid.UUID] = None
    timestamp: datetime = Field(validation_alias="observed_at")
    raw_plate: Optional[str] = None
    normalized_plate: Optional[str] = None
    plate_confidence: Optional[float] = None
    vehicle_confidence: Optional[float] = None
    frame_reference: Optional[str] = None
    detection_reference: Optional[str] = None
    inference_event_id: Optional[str] = None
    is_demo: bool = False
    anpr_claimed: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    
    # Frontend & Intelligence Compatibility Fields
    plate_number: Optional[str] = None
    raw_plate_text: Optional[str] = None
    confidence: Optional[float] = None
    vehicle_type: Optional[str] = None
    vehicle_color: Optional[str] = None
    vehicle_make: Optional[str] = None
    camera_name: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    speed_kmh: Optional[float] = None
    matched_watchlist: bool = False
    watchlist_type: Optional[str] = None
    snapshot_url: Optional[str] = None

    @model_validator(mode="after")
    def populate_compatibility_fields(self):
        if not self.plate_number:
            self.plate_number = self.normalized_plate or self.raw_plate or ""
        if not self.raw_plate_text:
            self.raw_plate_text = self.raw_plate or self.normalized_plate or ""
        if self.confidence is None:
            self.confidence = self.plate_confidence if self.plate_confidence is not None else 0.0
        if not self.snapshot_url and self.frame_reference:
            self.snapshot_url = self.frame_reference
        return self

    @field_validator("plate_confidence", "vehicle_confidence", "confidence", "latitude", "longitude", "speed_kmh", mode="before")
    @classmethod
    def num(cls, v):
        return float(v) if v is not None else v


class VehicleSearchHit(BaseModel):
    vehicle_id: uuid.UUID
    normalized_plate: str
    raw_plate: str
    first_seen_at: datetime
    last_seen_at: datetime
    total_sightings: int
    is_demo: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VehicleSighting(BaseModel):
    camera_id: uuid.UUID
    district: Optional[str] = None
    timestamp: datetime
    confidence: Optional[float] = None
    evidence_reference: Optional[str] = None
    is_demo: bool = False
    plate_confidence: Optional[float] = None
    vehicle_confidence: Optional[float] = None
    frame_reference: Optional[str] = None


class VehicleHistoryResponse(BaseModel):
    vehicle_id: uuid.UUID
    plate: str
    first_seen: datetime
    last_seen: datetime
    sightings: List[VehicleSighting]


class EvidenceResponse(BaseModel):
    """Public evidence metadata. Internal object keys / filesystem paths are not exposed."""

    evidence_id: uuid.UUID
    type: str
    storage_reference: str
    created_at: datetime
    hash: str
    algorithm: str
    camera_id: uuid.UUID
    timestamp: datetime
    is_demo: bool = False
    retention_days: Optional[int] = None
    file_format: Optional[str] = None
    file_size_bytes: Optional[int] = None
