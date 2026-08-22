from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.department import DepartmentResponse
from app.schemas.location import LocationResponse
from app.schemas.stream import CameraStreamResponse
from app.schemas.health import CameraHealthResponse

VALID_CAMERA_TYPES = {
    "ANPR", "PTZ", "FIXED", "IP", "BODY_WORN", "DRONE", "THERMAL", "OTHER"
}
VALID_CAMERA_STATUSES = {"ACTIVE", "INACTIVE", "MAINTENANCE", "DECOMMISSIONED"}
VALID_CONNECTIVITY_STATUSES = {"ONLINE", "DEGRADED", "OFFLINE", "UNKNOWN"}


class CameraBase(BaseModel):
    camera_code: str = Field(..., min_length=3, max_length=100, description="Unique camera identifier code")
    name: str = Field(..., min_length=2, max_length=255, description="Human-readable camera designation")
    department_id: uuid.UUID = Field(..., description="Owning government department ID")
    location_id: uuid.UUID = Field(..., description="Geographic installation location ID")
    camera_type: str = Field(..., description="Camera category (ANPR, PTZ, FIXED, IP, etc.)")
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    mac_address: Optional[str] = Field(None, max_length=50)
    ip_address: Optional[str] = Field(None, max_length=50)
    ownership: str = Field("Gujarat Government", max_length=100)
    installation_date: Optional[date] = None
    status: str = Field("ACTIVE", description="Lifecycle status (ACTIVE, INACTIVE, MAINTENANCE, DECOMMISSIONED)")
    connectivity_status: str = Field("ONLINE", description="Network reachability (ONLINE, DEGRADED, OFFLINE, UNKNOWN)")
    storage_type: str = Field("EDGE_AND_CENTRAL", max_length=50)
    retention_days: int = Field(30, gt=0, le=365)
    field_of_view_deg: Optional[float] = Field(None, ge=0.0, le=360.0)
    azimuth_angle_deg: Optional[float] = Field(None, ge=0.0, le=360.0)
    metadata: Dict = Field(default_factory=dict)
    
    # Source mapping fields
    source_system_id: Optional[uuid.UUID] = Field(None, description="External CCTV source system provider ID")
    source_camera_id: Optional[str] = Field(None, max_length=100, description="Raw camera ID in external source system")
    source_reference: Optional[str] = Field(None, max_length=255, description="External stream or device reference")
    source_metadata: Dict = Field(default_factory=dict, description="Raw external metadata from source provider")
    last_connected_at: Optional[datetime] = None

    @field_validator("camera_code")
    @classmethod
    def normalize_camera_code(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if not v_clean:
            raise ValueError("Camera code cannot be empty")
        return v_clean

    @field_validator("camera_type")
    @classmethod
    def validate_camera_type(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in VALID_CAMERA_TYPES:
            raise ValueError(f"Invalid camera_type: {v}. Must be one of {sorted(VALID_CAMERA_TYPES)}")
        return v_upper

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in VALID_CAMERA_STATUSES:
            raise ValueError(f"Invalid status: {v}. Must be one of {sorted(VALID_CAMERA_STATUSES)}")
        return v_upper

    @field_validator("connectivity_status")
    @classmethod
    def validate_connectivity(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in VALID_CONNECTIVITY_STATUSES:
            raise ValueError(f"Invalid connectivity_status: {v}. Must be one of {sorted(VALID_CONNECTIVITY_STATUSES)}")
        return v_upper

    @field_validator("ip_address", mode="before")
    @classmethod
    def serialize_ip(cls, v: Any) -> Optional[str]:
        if v is not None:
            return str(v)
        return None

    @field_validator("metadata", mode="before")
    @classmethod
    def extract_metadata(cls, v: Any) -> dict:
        if isinstance(v, dict):
            return v
        return {}


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    department_id: Optional[uuid.UUID] = None
    location_id: Optional[uuid.UUID] = None
    camera_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    ownership: Optional[str] = None
    installation_date: Optional[date] = None
    status: Optional[str] = None
    connectivity_status: Optional[str] = None
    storage_type: Optional[str] = None
    retention_days: Optional[int] = Field(None, gt=0, le=365)
    field_of_view_deg: Optional[float] = Field(None, ge=0.0, le=360.0)
    azimuth_angle_deg: Optional[float] = Field(None, ge=0.0, le=360.0)
    metadata: Optional[Dict] = None
    source_system_id: Optional[uuid.UUID] = None
    source_camera_id: Optional[str] = None
    source_reference: Optional[str] = None
    source_metadata: Optional[Dict] = None

    @field_validator("camera_type")
    @classmethod
    def validate_camera_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.strip().upper()
            if v_upper not in VALID_CAMERA_TYPES:
                raise ValueError(f"Invalid camera_type: {v}. Must be one of {sorted(VALID_CAMERA_TYPES)}")
            return v_upper
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.strip().upper()
            if v_upper not in VALID_CAMERA_STATUSES:
                raise ValueError(f"Invalid status: {v}. Must be one of {sorted(VALID_CAMERA_STATUSES)}")
            return v_upper
        return v

    @field_validator("connectivity_status")
    @classmethod
    def validate_connectivity(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.strip().upper()
            if v_upper not in VALID_CONNECTIVITY_STATUSES:
                raise ValueError(f"Invalid connectivity_status: {v}. Must be one of {sorted(VALID_CONNECTIVITY_STATUSES)}")
            return v_upper
        return v


class CameraResponse(CameraBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CameraDetailResponse(CameraResponse):
    department: Optional[DepartmentResponse] = None
    location: Optional[LocationResponse] = None
    streams: List[CameraStreamResponse] = Field(default_factory=list)
    current_health: Optional[CameraHealthResponse] = None


class CameraNearbyResponse(BaseModel):
    camera_id: uuid.UUID
    camera_code: str
    name: str
    camera_type: str
    status: str
    connectivity_status: str
    location_id: uuid.UUID
    location_name: str
    district: str
    city: str
    latitude: float
    longitude: float
    distance_meters: float
    primary_stream_protocol: Optional[str] = None


class CameraCoverageResponse(BaseModel):
    total_cameras: int
    cameras_by_department: Dict[str, int]
    cameras_by_district: Dict[str, int]
    cameras_by_status: Dict[str, int]
    cameras_by_type: Dict[str, int]
    online_percentage: float
    timestamp: datetime


class CameraBulkImportRow(BaseModel):
    camera_code: str
    name: str
    department_code: str
    location_name: str
    district: str
    city: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    camera_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    ownership: str = "Gujarat Government"
    stream_url: Optional[str] = None
    protocol: Optional[str] = "RTSP"


class BulkImportErrorDetail(BaseModel):
    row: int
    field: Optional[str] = None
    error: str
    data: Optional[Dict[str, Any]] = None


class CameraBulkImportResponse(BaseModel):
    total_rows: int
    successful: int
    failed: int
    errors: List[BulkImportErrorDetail] = Field(default_factory=list)
    imported_camera_codes: List[str] = Field(default_factory=list)
