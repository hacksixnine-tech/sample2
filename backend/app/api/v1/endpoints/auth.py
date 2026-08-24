from datetime import datetime, timezone
from typing import Any, Dict
import uuid
from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import (
    Principal,
    get_permissions_for_roles,
    get_principal,
    resolve_principal,
)
from app.core.config import settings
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.dependencies import get_db
from app.models.user import User, Role
from app.repositories.audit import audit_repo
from app.repositories.user import user_repo
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserProfileResponse,
)
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate User and Issue JWT Tokens",
)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """
    Authenticate user using username or email and bcrypt password hash.
    Sets last_login_at timestamp, logs LOGIN audit event, and returns JWT tokens.
    """
    user = await user_repo.get_by_identifier(db, login_data.username)
    if not user:
        # Record failed login attempt in audit
        await audit_repo.log_action(
            session=db,
            action="SECURITY_VIOLATION",
            resource_type="AUTH",
            resource_id=login_data.username,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details=f"Failed login attempt for non-existent user identifier: {login_data.username}",
        )
        await db.commit()
        raise AuthenticationError("Invalid username or password")

    if not verify_password(login_data.password, user.password_hash):
        await audit_repo.log_action(
            session=db,
            action="SECURITY_VIOLATION",
            resource_type="AUTH",
            resource_id=str(user.id),
            user_id=user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details=f"Failed password verification for user {user.username}",
        )
        await db.commit()
        raise AuthenticationError("Invalid username or password")

    if not user.is_active:
        await audit_repo.log_action(
            session=db,
            action="SECURITY_VIOLATION",
            resource_type="AUTH",
            resource_id=str(user.id),
            user_id=user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details=f"Login attempt by deactivated account: {user.username}",
        )
        await db.commit()
        raise AuthenticationError("Account is inactive. Please contact system administrator.")

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)

    role_name = user.role.name if user.role else "VIEWER"
    dept_name = user.department.name if user.department else None

    # Audit Trail Logging
    await audit_repo.log_action(
        session=db,
        action="LOGIN",
        resource_type="AUTH",
        resource_id=str(user.id),
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=f"User {user.username} ({role_name}) logged in successfully",
    )
    await db.commit()
    await db.refresh(user)

    # JWT Claims
    extra_claims = {
        "role": role_name,
        "department_id": str(user.department_id),
        "username": user.username,
        "badge_number": user.badge_number,
    }

    access_token = create_access_token(subject=str(user.id), extra_claims=extra_claims)
    refresh_token = create_refresh_token(subject=str(user.id))

    permissions = get_permissions_for_roles([role_name])
    if user.role and user.role.permissions:
        if "*" in user.role.permissions:
            permissions = ["*"]
        else:
            permissions = sorted(list(set(permissions + user.role.permissions)))

    user_info = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "badge_number": user.badge_number,
        "phone_number": user.phone_number,
        "role": role_name,
        "department_id": str(user.department_id),
        "department_name": dept_name,
        "is_active": user.is_active,
        "permissions": permissions,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }

    return ApiResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_info,
        ),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token using Refresh Token",
)
async def refresh_token(
    refresh_req: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """Validate refresh token and issue renewed access token."""
    try:
        payload = decode_token(refresh_req.refresh_token)
    except ValueError as exc:
        raise AuthenticationError(f"Invalid refresh token: {str(exc)}") from exc

    if payload.get("type") != "refresh":
        raise AuthenticationError("Provided token is not a refresh token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("Refresh token missing subject")

    try:
        user_id = uuid.UUID(user_id_str)
    except Exception:
        raise AuthenticationError("Invalid subject in refresh token")

    user = await user_repo.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User not found or account deactivated")

    role_name = user.role.name if user.role else "VIEWER"
    dept_name = user.department.name if user.department else None

    extra_claims = {
        "role": role_name,
        "department_id": str(user.department_id),
        "username": user.username,
        "badge_number": user.badge_number,
    }

    new_access_token = create_access_token(subject=str(user.id), extra_claims=extra_claims)
    new_refresh_token = create_refresh_token(subject=str(user.id))

    permissions = get_permissions_for_roles([role_name])
    if user.role and user.role.permissions:
        if "*" in user.role.permissions:
            permissions = ["*"]
        else:
            permissions = sorted(list(set(permissions + user.role.permissions)))

    user_info = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "badge_number": user.badge_number,
        "phone_number": user.phone_number,
        "role": role_name,
        "department_id": str(user.department_id),
        "department_name": dept_name,
        "is_active": user.is_active,
        "permissions": permissions,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }

    return ApiResponse(
        success=True,
        data=TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_info,
        ),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/logout",
    response_model=ApiResponse[Dict[str, str]],
    status_code=status.HTTP_200_OK,
    summary="Log Out and Invalidate Session",
)
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
) -> ApiResponse[Dict[str, str]]:
    """Log user logout in the centralized immutable audit log."""
    await audit_repo.log_action(
        session=db,
        action="LOGOUT",
        resource_type="AUTH",
        resource_id=str(principal.user_id) if principal.user_id else principal.subject,
        user_id=principal.user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=f"User {principal.subject} logged out",
    )
    await db.commit()

    return ApiResponse(
        success=True,
        data={"message": "Logged out successfully"},
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserProfileResponse],
    summary="Get Current Authenticated User Profile",
)
async def get_current_user_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
) -> ApiResponse[UserProfileResponse]:
    """Retrieve full profile details, role, department, and granted permissions."""
    if not principal.user_id:
        # Worker or machine principal
        return ApiResponse(
            success=True,
            data=UserProfileResponse(
                id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                username=principal.subject,
                full_name="Internal Service Account",
                role=principal.roles[0] if principal.roles else "AI_WORKER",
                department_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                is_active=True,
                permissions=principal.permissions,
                metadata={"principal_type": principal.principal_type},
            ),
            request_id=getattr(request.state, "request_id", None),
        )

    user = await user_repo.get_by_id(db, principal.user_id)
    if not user:
        raise NotFoundError("User profile not found")

    role_name = user.role.name if user.role else "VIEWER"
    dept_name = user.department.name if user.department else None

    permissions = get_permissions_for_roles([role_name])
    if user.role and user.role.permissions:
        if "*" in user.role.permissions:
            permissions = ["*"]
        else:
            permissions = sorted(list(set(permissions + user.role.permissions)))

    return ApiResponse(
        success=True,
        data=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            badge_number=user.badge_number,
            phone_number=user.phone_number,
            role=role_name,
            department_id=user.department_id,
            department_name=dept_name,
            is_active=user.is_active,
            permissions=permissions,
            metadata=user.metadata_,
        ),
        request_id=getattr(request.state, "request_id", None),
    )
