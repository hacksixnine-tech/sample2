from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


VALID_ALERT_STATES = {"NEW", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "DISMISSED"}
VALID_SEVERITIES = {"LOW", "INFO", "MEDIUM", "HIGH", "CRITICAL"}

VALID_STATE_TRANSITIONS = {
    "NEW": {"ACKNOWLEDGED", "INVESTIGATING", "DISMISSED"},
    "ACKNOWLEDGED": {"INVESTIGATING", "RESOLVED", "DISMISSED"},
    "INVESTIGATING": {"RESOLVED", "DISMISSED"},
    "RESOLVED": set(),  # Terminal state
    "DISMISSED": set(), # Terminal state
}


class AlertReason(BaseModel):
    type: str = "WATCHLIST_MATCH"
    match_type: str = "EXACT_PLATE"
    plate: Optional[str] = None
    confidence: Optional[float] = None
    watchlist: Optional[str] = None
    watchlist_id: Optional[uuid.UUID] = None
    camera: Optional[str] = None
    camera_id: Optional[uuid.UUID] = None
    district: Optional[str] = None
    timestamp: Optional[datetime] = None
    explanation: Optional[str] = None


class AlertBase(BaseModel):
    alert_type: str = Field(default="WATCHLIST_HIT", examples=["WATCHLIST_HIT"])
    severity: str = Field(default="HIGH", examples=["HIGH", "CRITICAL"])
    title: str = Field(..., examples=["Stolen Vehicle Detected: GJ01AB1234"])
    message: str = Field(..., examples=["Vehicle matched active hotlist at SG Highway Camera 04"])
    status: str = Field(default="NEW", examples=["NEW"])
    camera_id: uuid.UUID
    entity_id: Optional[uuid.UUID] = None
    source_match_id: Optional[uuid.UUID] = None
    source_event_id: Optional[uuid.UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AlertCreate(AlertBase):
    alert_code: Optional[str] = None
    reason: Optional[AlertReason] = None


class AlertUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AlertAcknowledgeRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Investigator acknowledgement notes")


class AlertResolutionRequest(BaseModel):
    resolution_notes: str = Field(..., description="Action taken summary", examples=["Interception team deployed, vehicle detained."])


class AlertDismissRequest(BaseModel):
    dismissal_reason: str = Field(..., description="Reason for dismissal", examples=["False positive plate recognition read."])


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    alert_code: str
    alert_type: str
    severity: str
    title: str
    message: str
    status: str
    camera_id: uuid.UUID
    camera_name: Optional[str] = None
    district: Optional[str] = None
    entity_id: Optional[uuid.UUID] = None
    source_match_id: Optional[uuid.UUID] = None
    source_event_id: Optional[uuid.UUID] = None
    acknowledged_by_user_id: Optional[uuid.UUID] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by_user_id: Optional[uuid.UUID] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    reason: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    created_at: datetime
    updated_at: datetime
