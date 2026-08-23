from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class DistrictBase(BaseModel):
    district_code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    state: str = Field(default="Gujarat", max_length=100)
    zone: Optional[str] = Field(None, max_length=100)
    headquarters: Optional[str] = Field(None, max_length=100)
    centroid_lat: float = Field(..., ge=-90.0, le=90.0)
    centroid_lng: float = Field(..., ge=-180.0, le=180.0)
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DistrictCreate(DistrictBase):
    pass


class DistrictUpdate(BaseModel):
    district_code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    zone: Optional[str] = None
    headquarters: Optional[str] = None
    centroid_lat: Optional[float] = Field(None, ge=-90.0, le=90.0)
    centroid_lng: Optional[float] = Field(None, ge=-180.0, le=180.0)
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class DistrictResponse(DistrictBase):
    id: uuid.UUID
    camera_count: Optional[int] = Field(default=0)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
