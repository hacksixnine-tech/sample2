from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


VALID_INCIDENT_STATES = {"OPEN", "INVESTIGATING", "IN_PROGRESS", "CONTAINED", "ESCALATED", "CLOSED", "ARCHIVED"}
VALID_INCIDENT_TRANSITIONS = {
    "OPEN": {"INVESTIGATING", "IN_PROGRESS", "ESCALATED", "CONTAINED", "CLOSED"},
    "INVESTIGATING": {"IN_PROGRESS", "ESCALATED", "CONTAINED", "CLOSED"},
    "IN_PROGRESS": {"INVESTIGATING", "ESCALATED", "CONTAINED", "CLOSED"},
    "CONTAINED": {"CLOSED", "INVESTIGATING"},
    "ESCALATED": {"INVESTIGATING", "CONTAINED", "CLOSED"},
    "CLOSED": {"ARCHIVED", "OPEN"},
    "ARCHIVED": set(),
}


class IncidentBase(BaseModel):
    title: str = Field(..., examples=["Armed Robbery Vehicle Escape Corridor"])
    description: str = Field(..., examples=["Vehicle GJ01AB1234 identified fleeing scene across SG Highway"])
    severity: str = Field(default="HIGH", description="LOW, MEDIUM, HIGH, CRITICAL")
    status: str = Field(default="OPEN", description="OPEN, INVESTIGATING, CONTAINED, CLOSED, ARCHIVED")
    assigned_department_id: Optional[uuid.UUID] = None
    assigned_user_id: Optional[uuid.UUID] = None
    occurred_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentCreate(IncidentBase):
    incident_code: Optional[str] = None
    alert_ids: Optional[List[uuid.UUID]] = None
    event_ids: Optional[List[uuid.UUID]] = None
    evidence_ids: Optional[List[uuid.UUID]] = None
    entity_ids: Optional[List[uuid.UUID]] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    assigned_department_id: Optional[uuid.UUID] = None
    assigned_user_id: Optional[uuid.UUID] = None
    closing_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LinkNotesRequest(BaseModel):
    notes: Optional[str] = None
    involvement_role: Optional[str] = "SUSPECT"


class LinkedAlertResponse(BaseModel):
    alert_id: uuid.UUID
    alert_code: Optional[str] = None
    title: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    added_at: datetime
    notes: Optional[str] = None


class LinkedEventResponse(BaseModel):
    event_id: uuid.UUID
    event_type: Optional[str] = None
    occurred_at: Optional[datetime] = None
    added_at: datetime
    notes: Optional[str] = None


class LinkedEntityResponse(BaseModel):
    entity_id: uuid.UUID
    primary_identifier: Optional[str] = None
    entity_type: Optional[str] = None
    involvement_role: str
    added_at: datetime
    notes: Optional[str] = None


class LinkedEvidenceResponse(BaseModel):
    evidence_id: uuid.UUID
    evidence_code: Optional[str] = None
    evidence_type: Optional[str] = None
    added_at: datetime
    notes: Optional[str] = None


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    incident_code: str
    title: str
    description: str
    severity: str
    status: str
    assigned_department_id: Optional[uuid.UUID] = None
    assigned_department_name: Optional[str] = None
    assigned_user_id: Optional[uuid.UUID] = None
    assigned_user_name: Optional[str] = None
    occurred_at: datetime
    closed_at: Optional[datetime] = None
    closing_notes: Optional[str] = None
    alerts_count: int = 0
    events_count: int = 0
    entities_count: int = 0
    evidence_count: int = 0
    alerts: Optional[List[LinkedAlertResponse]] = None
    events: Optional[List[LinkedEventResponse]] = None
    entities: Optional[List[LinkedEntityResponse]] = None
    evidence: Optional[List[LinkedEvidenceResponse]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    created_at: datetime
    updated_at: datetime
