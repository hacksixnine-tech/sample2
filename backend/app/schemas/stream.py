from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator

SUPPORTED_PROTOCOLS = {"RTSP", "HLS", "WEBRTC", "HTTP", "ONVIF", "VENDOR_API", "OTHER"}


class CameraStreamBase(BaseModel):
    protocol: str = Field(..., description="Streaming protocol (RTSP, HLS, WEBRTC, HTTP, ONVIF, VENDOR_API, OTHER)")
    stream_url: str = Field(..., min_length=5, max_length=500, description="Stream URL or Ingest endpoint")
    secret_ref: Optional[str] = Field(None, max_length=255, description="Vault secret key pointer (no plaintext passwords)")
    resolution: str = Field("1080p", max_length=50)
    fps: float = Field(25.0, gt=0, le=120, description="Frames per second")
    codec: str = Field("H264", max_length=50)
    bitrate_kbps: Optional[int] = Field(None, ge=0)
    is_primary: bool = Field(True, description="Primary live stream flag")
    is_active: bool = Field(True, description="Stream active flag")
    metadata: Dict = Field(default_factory=dict)

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in SUPPORTED_PROTOCOLS:
            raise ValueError(f"Unsupported protocol: {v}. Must be one of {sorted(SUPPORTED_PROTOCOLS)}")
        return v_upper

    @field_validator("stream_url")
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


class CameraStreamCreate(CameraStreamBase):
    pass


class CameraStreamUpdate(BaseModel):
    protocol: Optional[str] = None
    stream_url: Optional[str] = Field(None, min_length=5, max_length=500)
    secret_ref: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[float] = Field(None, gt=0, le=120)
    codec: Optional[str] = None
    bitrate_kbps: Optional[int] = Field(None, ge=0)
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict] = None

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.strip().upper()
            if v_upper not in SUPPORTED_PROTOCOLS:
                raise ValueError(f"Unsupported protocol: {v}. Must be one of {sorted(SUPPORTED_PROTOCOLS)}")
            return v_upper
        return v


class CameraStreamResponse(CameraStreamBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    camera_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
