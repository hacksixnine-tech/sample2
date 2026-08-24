from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: str = Field(..., description="User login identifier or email")
    password: str = Field(..., min_length=1, description="Plaintext password to authenticate")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int
    user: Dict[str, Any]


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid signed JWT refresh token")


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: Optional[str] = None
    full_name: str
    badge_number: Optional[str] = None
    phone_number: Optional[str] = None
    role: str
    department_id: uuid.UUID
    department_name: Optional[str] = None
    is_active: bool
    permissions: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)
