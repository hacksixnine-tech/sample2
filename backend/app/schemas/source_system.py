from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceSystemBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="External source provider name")
    code: str = Field(..., min_length=2, max_length=100, description="Unique uppercase source system code")
    base_url: str = Field(..., min_length=5, max_length=500, description="Base API / Web endpoint URL")
    source_type: str = Field("EXTERNAL_PROVIDED_CCTV_SOURCE", max_length=100)
    status: str = Field("ACTIVE", description="ACTIVE, INACTIVE, DEGRADED, MAINTENANCE")
    auth_config: Dict = Field(default_factory=dict, description="Secure auth credentials / headers pointer")
    metadata: Dict = Field(default_factory=dict, description="Provider metadata")

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if not v_clean:
            raise ValueError("Source system code cannot be empty")
        return v_clean

    @field_validator("base_url")
    @classmethod
    def validate_url_safety(cls, v: str) -> str:
        from app.core.validators import validate_safe_url
        return validate_safe_url(v)

    @field_validator("metadata", mode="before")
    @classmethod
    def extract_metadata(cls, v: Any) -> dict:
        if isinstance(v, dict):
            return v
        return {}


class SourceSystemCreate(SourceSystemBase):
    pass


class SourceSystemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    base_url: Optional[str] = Field(None, min_length=5, max_length=500)
    source_type: Optional[str] = None
    status: Optional[str] = None
    auth_config: Optional[Dict] = None
    metadata: Optional[Dict] = None


class SourceSystemResponse(SourceSystemBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DiscoveredStream(BaseModel):
    protocol: str
    stream_url: str
    resolution: str = "1080p"
    fps: float = 25.0
    codec: str = "H264"
    bitrate_kbps: Optional[int] = None
    is_primary: bool = False


class SourceDiscoveryCamera(BaseModel):
    source_camera_id: str
    number: Optional[int] = None
    name: str
    raw_location_string: Optional[str] = None
    inferred_district: str = "UNKNOWN"
    inferred_city: str = "UNKNOWN"
    status: str
    delivery: str
    streams: List[DiscoveredStream] = Field(default_factory=list)
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceDiscoveryResponse(BaseModel):
    source_system_id: uuid.UUID
    source_name: str
    base_url: str
    total_discovered: int
    catalog_state: str
    scanned_at: datetime
    cameras: List[SourceDiscoveryCamera] = Field(default_factory=list)


class SourceSyncResponse(BaseModel):
    source_system_id: uuid.UUID
    total_discovered: int
    created_count: int
    updated_count: int
    error_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    synced_camera_codes: List[str] = Field(default_factory=list)
