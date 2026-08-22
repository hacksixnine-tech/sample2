from datetime import datetime
from typing import Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Full department name")
    code: str = Field(..., min_length=2, max_length=50, description="Unique uppercase department code")
    description: Optional[str] = Field(None, max_length=1000, description="Department purpose description")
    contact_email: Optional[str] = Field(None, max_length=255, description="Contact email address")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Contact telephone")
    is_active: bool = Field(True, description="Active department status")

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if not v_clean:
            raise ValueError("Department code cannot be empty or whitespace")
        return v_clean

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("Department name cannot be empty or whitespace")
        return v_clean


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = Field(None)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip()
            if not v_clean:
                raise ValueError("Department name cannot be empty")
            return v_clean
        return v


class DepartmentResponse(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DepartmentCameraSummaryResponse(BaseModel):
    department_id: uuid.UUID
    department_code: str
    department_name: str
    total_cameras: int
    online_cameras: int
    offline_cameras: int
    degraded_cameras: int
    maintenance_cameras: int
    camera_types: Dict[str, int]
    district_distribution: Dict[str, int]
