from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator

HEALTH_STATUSES = {"ONLINE", "DEGRADED", "OFFLINE", "MAINTENANCE", "UNKNOWN"}


class HealthResponse(BaseModel):
    status: str = Field("healthy", description="Overall health status (healthy/degraded)")
    timestamp: datetime = Field(..., description="UTC timestamp of the health check")
    environment: str = Field(..., description="Active runtime environment")
    version: str = Field(..., description="API version")


class ReadinessResponse(BaseModel):
    status: str = Field(..., description="Readiness status (ready/not_ready)")
    timestamp: datetime = Field(..., description="UTC timestamp of the readiness check")
    database: Dict[str, Any] = Field(..., description="Database connection telemetry")


class InfoResponse(BaseModel):
    application: str = Field(..., description="Application name")
    version: str = Field(..., description="Application semantic version")
    environment: str = Field(..., description="Runtime environment")
    api_prefix: str = Field(..., description="Base API path prefix")
    timestamp: datetime = Field(..., description="Current UTC timestamp")
    active_modules: List[str] = Field(..., description="List of initialized backend modules")


class CameraHealthCreate(BaseModel):
    status: str = Field(..., description="Health status (ONLINE, DEGRADED, OFFLINE, MAINTENANCE, UNKNOWN)")
    latency_ms: Optional[int] = Field(None, ge=0, description="Ping latency in milliseconds")
    packet_loss_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Packet loss percentage")
    current_fps: Optional[float] = Field(None, ge=0.0, description="Current stream FPS")
    bitrate_kbps: Optional[int] = Field(None, ge=0, description="Bitrate in kbps")
    health_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Composite health score (0-100)")
    last_error: Optional[str] = Field(None, description="Diagnostic error message if degraded/offline")
    metadata: Dict = Field(default_factory=dict)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in HEALTH_STATUSES:
            raise ValueError(f"Invalid health status: {v}. Must be one of {sorted(HEALTH_STATUSES)}")
        return v_upper

    @field_validator("metadata", mode="before")
    @classmethod
    def extract_metadata(cls, v: Any) -> dict:
        if isinstance(v, dict):
            return v
        return {}


class CameraHealthResponse(CameraHealthCreate):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    camera_id: uuid.UUID
    last_seen_at: datetime
    checked_at: datetime


class CameraHealthSummaryResponse(BaseModel):
    total: int = Field(..., description="Total registered cameras")
    online: int = Field(..., description="Cameras reporting ONLINE status")
    degraded: int = Field(..., description="Cameras reporting DEGRADED performance")
    offline: int = Field(..., description="Cameras reporting OFFLINE state")
    maintenance: int = Field(..., description="Cameras in MAINTENANCE mode")
    unknown: int = Field(0, description="Cameras with UNKNOWN health state")
    timestamp: datetime = Field(..., description="Timestamp when summary was compiled")
