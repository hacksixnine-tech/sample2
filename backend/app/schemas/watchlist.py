from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


VALID_WATCHLIST_CATEGORIES = {
    "STOLEN_VEHICLES",
    "WANTED_VEHICLES",
    "BLACKLISTED_VEHICLES",
    "WANTED_PERSONS",
    "MISSING_PERSONS",
    "SUSPECT_WATCHLIST",
    "TRAFFIC_OFFENDERS",
    "VIP_MONITORING",
    "OTHER",
    "STOLEN_VEHICLE",
    "WANTED_VEHICLE",
    "BLACKLISTED_VEHICLE",
    "WANTED_PERSON",
    "MISSING_PERSON",
    "SUSPECT",
    "CUSTOM",
}


def normalize_watchlist_category(category: str) -> str:
    cat = category.strip().upper()
    mapping = {
        "STOLEN_VEHICLE": "STOLEN_VEHICLES",
        "WANTED_VEHICLE": "WANTED_VEHICLES",
        "BLACKLISTED_VEHICLE": "BLACKLISTED_VEHICLES",
        "WANTED_PERSON": "WANTED_PERSONS",
        "MISSING_PERSON": "MISSING_PERSONS",
        "SUSPECT": "SUSPECT_WATCHLIST",
        "CUSTOM": "OTHER",
    }
    return mapping.get(cat, cat)


class WatchlistEntryBase(BaseModel):
    identifier: str = Field(..., description="Plate number, person name, or target token", examples=["GJ01AB1234"])
    entity_type: str = Field(default="VEHICLE", description="VEHICLE, PERSON, OBJECT, OTHER")
    case_reference_number: Optional[str] = Field(None, examples=["FIR-4421/2026"])
    fir_station: Optional[str] = Field(None, examples=["Navrangpura Police Station"])
    reason: str = Field(..., description="Legal rationale / warrant reference", examples=["Stolen under IPC 379"])
    priority: str = Field(default="HIGH", description="LOW, MEDIUM, HIGH, CRITICAL")
    valid_from: Optional[datetime] = Field(None, description="Start time of active watchlist validity")
    valid_until: Optional[datetime] = Field(None, description="Expiration time of active watchlist validity")
    is_active: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WatchlistEntryCreate(WatchlistEntryBase):
    raw_plate: Optional[str] = None
    normalized_plate: Optional[str] = None
    external_reference: Optional[str] = None
    notes: Optional[str] = None


class WatchlistEntryUpdate(BaseModel):
    identifier: Optional[str] = None
    case_reference_number: Optional[str] = None
    fir_station: Optional[str] = None
    reason: Optional[str] = None
    priority: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class WatchlistEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    watchlist_id: uuid.UUID
    identifier: str
    normalized_identifier: str
    entity_type: str
    case_reference_number: Optional[str] = None
    fir_station: Optional[str] = None
    reason: str
    priority: str
    valid_from: datetime
    valid_until: Optional[datetime] = None
    is_active: bool
    status: str = "ACTIVE"
    metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    created_at: datetime
    updated_at: datetime


class WatchlistBase(BaseModel):
    name: str = Field(..., examples=["Ahmedabad Stolen Four Wheelers Hotlist"])
    code: Optional[str] = Field(None, examples=["WL-AHM-STOLEN-4W"])
    category: str = Field(..., examples=["STOLEN_VEHICLE"])
    department_id: Optional[uuid.UUID] = Field(None, description="Department UUID")
    owner_department: Optional[str] = Field(None, description="Department code or name alias")
    description: Optional[str] = Field(None, examples=["Hotlist for stolen light motor vehicles"])
    priority: str = Field(default="HIGH", description="LOW, MEDIUM, HIGH, CRITICAL")
    is_active: bool = Field(default=True)
    active: Optional[bool] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WatchlistCreate(WatchlistBase):
    pass


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    is_active: Optional[bool] = None
    active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class WatchlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    name: str
    code: str
    category: str
    department_id: uuid.UUID
    owner_department: Optional[str] = None
    description: Optional[str] = None
    priority: str
    is_active: bool
    active: Optional[bool] = None
    entry_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    created_at: datetime
    updated_at: datetime
    entries: Optional[List[WatchlistEntryResponse]] = None
