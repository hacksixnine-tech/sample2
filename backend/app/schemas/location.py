from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


class LocationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Location/Junction name")
    state: str = Field("Gujarat", max_length=100, description="State name")
    district: str = Field(..., min_length=2, max_length=100, description="Gujarat district")
    taluka: Optional[str] = Field(None, max_length=100)
    city: str = Field(..., min_length=2, max_length=100, description="City / Municipality")
    zone: Optional[str] = Field(None, max_length=100)
    ward: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=1000)
    landmark: Optional[str] = Field(None, max_length=500)
    postal_code: Optional[str] = Field(None, max_length=20)
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to +90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to +180)")
    metadata: Dict = Field(default_factory=dict, description="Custom geographic metadata")

    @field_validator("name", "district", "city")
    @classmethod
    def normalize_string_fields(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("Field cannot be empty or whitespace")
        return v_clean

    @field_validator("metadata", mode="before")
    @classmethod
    def extract_metadata(cls, v: Any) -> dict:
        if isinstance(v, dict):
            return v
        return {}


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    state: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    taluka: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    zone: Optional[str] = Field(None, max_length=100)
    ward: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=1000)
    landmark: Optional[str] = Field(None, max_length=500)
    postal_code: Optional[str] = Field(None, max_length=20)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    metadata: Optional[Dict] = None


class LocationResponse(LocationBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class NearbyLocationResponse(BaseModel):
    location_id: uuid.UUID
    name: str
    district: str
    city: str
    latitude: float
    longitude: float
    distance_meters: float
    camera_count: int = 0
