from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, EmailStr, Field


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    permissions: List[str]


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6, description="Initial user password")
    full_name: str = Field(..., min_length=1, max_length=255)
    badge_number: Optional[str] = None
    phone_number: Optional[str] = None
    department_id: uuid.UUID
    role_id: Optional[uuid.UUID] = None
    role_name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    badge_number: Optional[str] = None
    phone_number: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    role_id: Optional[uuid.UUID] = None
    role_name: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class PasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=6, description="New secure password")


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: Optional[str] = None
    full_name: str
    badge_number: Optional[str] = None
    phone_number: Optional[str] = None
    department_id: uuid.UUID
    department_name: Optional[str] = None
    role_id: uuid.UUID
    role_name: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[UserResponse]
