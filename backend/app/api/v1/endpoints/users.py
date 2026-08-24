from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import (
    Principal,
    get_principal,
    require_system_admin,
    require_user_manage,
)
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.core.security import get_password_hash
from app.db.dependencies import get_db
from app.models.department import Department
from app.models.user import Role, User
from app.repositories.audit import audit_repo
from app.repositories.user import role_repo, user_repo
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
from app.schemas.user import (
    PasswordResetRequest,
    RoleResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Users & Access Governance"])


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        badge_number=user.badge_number,
        phone_number=user.phone_number,
        department_id=user.department_id,
        department_name=user.department.name if user.department else None,
        role_id=user.role_id,
        role_name=user.role.name if user.role else "VIEWER",
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        metadata=user.metadata_,
    )


@router.get(
    "/roles",
    response_model=ApiResponse[List[RoleResponse]],
    summary="List System Roles and Granted Permissions",
)
async def list_roles(
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
) -> ApiResponse[List[RoleResponse]]:
    """List all available roles and their configured permission sets."""
    roles = await role_repo.list_all_roles(db)
    role_list = [
        RoleResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            permissions=r.permissions,
        )
        for r in roles
    ]
    return ApiResponse(
        success=True,
        data=role_list,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="List Users with Search and Filtering",
)
async def list_users(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    department_id: Optional[uuid.UUID] = Query(None, description="Filter by department"),
    role_id: Optional[uuid.UUID] = Query(None, description="Filter by role ID"),
    role_name: Optional[str] = Query(None, description="Filter by role name (e.g. POLICE_OFFICER)"),
    is_active: Optional[bool] = Query(None, description="Filter active/deactivated users"),
    search: Optional[str] = Query(None, description="Search across username, full name, email, badge"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_user_manage),
) -> PaginatedResponse[UserResponse]:
    """List system users with pagination, role/department filters, and search capabilities."""
    offset = (page - 1) * page_size
    users, total = await user_repo.list_users(
        session=db,
        department_id=department_id,
        role_id=role_id,
        role_name=role_name,
        is_active=is_active,
        search=search,
        offset=offset,
        limit=page_size,
    )
    items = [_to_user_response(u) for u in users]
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        success=True,
        data=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create New User with Role & Department Assignment",
)
async def create_user(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_user_manage),
) -> ApiResponse[UserResponse]:
    """
    Create a new system user with hashed password and role assignment.
    Applies Privilege Escalation Protection: Only SYSTEM_ADMIN can create SYSTEM_ADMIN accounts.
    """
    # 1. Check uniqueness
    existing_username = await user_repo.get_by_username(db, user_in.username)
    if existing_username:
        raise ConflictError(f"Username '{user_in.username}' is already registered")

    if user_in.email:
        existing_email = await user_repo.get_by_email(db, user_in.email)
        if existing_email:
            raise ConflictError(f"Email '{user_in.email}' is already registered")

    # 2. Resolve Role
    target_role: Optional[Role] = None
    if user_in.role_id:
        target_role = await role_repo.get_by_id(db, user_in.role_id)
    elif user_in.role_name:
        target_role = await role_repo.get_by_name(db, user_in.role_name)
    else:
        target_role = await role_repo.get_by_name(db, "VIEWER")

    if not target_role:
        raise ValidationError("Specified role was not found")

    # Privilege Escalation Protection: non-SYSTEM_ADMIN cannot create SYSTEM_ADMIN
    if target_role.name.upper() == "SYSTEM_ADMIN" and "SYSTEM_ADMIN" not in principal.roles:
        raise PermissionDeniedError("Only SYSTEM_ADMIN users can create administrative accounts")

    # 3. Verify Department
    dept_stmt = select(Department).where(Department.id == user_in.department_id)
    dept_res = await db.execute(dept_stmt)
    dept = dept_res.scalars().first()
    if not dept:
        raise ValidationError("Specified department was not found")

    # 4. Hash password and create User
    hashed_pwd = get_password_hash(user_in.password)
    user = User(
        username=user_in.username.strip(),
        email=user_in.email.strip().lower() if user_in.email else None,
        password_hash=hashed_pwd,
        full_name=user_in.full_name.strip(),
        badge_number=user_in.badge_number.strip() if user_in.badge_number else None,
        phone_number=user_in.phone_number.strip() if user_in.phone_number else None,
        department_id=dept.id,
        role_id=target_role.id,
        is_active=True,
        metadata_=user_in.metadata,
    )
    db.add(user)
    await db.flush()

    # 5. Audit Trail
    await audit_repo.log_action(
        session=db,
        action="CREATE_USER" if "CREATE_USER" in audit_repo.__class__.__name__ else "OTHER",
        resource_type="USER",
        resource_id=str(user.id),
        user_id=principal.user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=f"Created user {user.username} with role {target_role.name}",
    )
    await db.commit()
    await db.refresh(user)

    return ApiResponse(
        success=True,
        data=_to_user_response(user),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    summary="Get User Details by ID",
)
async def get_user(
    user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
) -> ApiResponse[UserResponse]:
    """Retrieve specific user details. Requires user management rights or self inspection."""
    if principal.user_id != user_id and "SYSTEM_ADMIN" not in principal.roles and not principal.has_permission("user:manage"):
        raise PermissionDeniedError("Insufficient role to view other user profiles")

    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise NotFoundError(f"User with ID {user_id} not found")

    return ApiResponse(
        success=True,
        data=_to_user_response(user),
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    summary="Update User Profile with Privilege Escalation Protection",
)
async def update_user(
    user_id: uuid.UUID,
    user_update: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
) -> ApiResponse[UserResponse]:
    """
    Update user profile, status, or role.
    Strict Privilege Escalation Protection:
    - Non-admins cannot promote any user to SYSTEM_ADMIN.
    - Non-admins cannot modify any user with SYSTEM_ADMIN role.
    - Non-admins cannot deactivate administrators or alter role permissions.
    """
    is_admin = "SYSTEM_ADMIN" in principal.roles or principal.has_permission("*")
    is_user_manager = is_admin or principal.has_permission("user:manage")
    is_self = principal.user_id == user_id

    if not is_user_manager and not is_self:
        raise PermissionDeniedError("Insufficient permissions to update this user")

    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise NotFoundError(f"User with ID {user_id} not found")

    target_user_is_admin = user.role and user.role.name.upper() == "SYSTEM_ADMIN"

    # Privilege Escalation Guard 1: Non-admins cannot modify an existing SYSTEM_ADMIN
    if target_user_is_admin and not is_admin:
        raise PermissionDeniedError("Only SYSTEM_ADMIN users can modify administrative accounts")

    # Privilege Escalation Guard 2: Non-managers cannot change role, department, or active status
    if not is_user_manager:
        if user_update.role_id is not None or user_update.role_name is not None:
            raise PermissionDeniedError("You do not have permission to change user roles")
        if user_update.is_active is not None:
            raise PermissionDeniedError("You do not have permission to change account active status")
        if user_update.department_id is not None:
            raise PermissionDeniedError("You do not have permission to change department assignment")

    # Role update handling
    if user_update.role_id or user_update.role_name:
        new_role: Optional[Role] = None
        if user_update.role_id:
            new_role = await role_repo.get_by_id(db, user_update.role_id)
        elif user_update.role_name:
            new_role = await role_repo.get_by_name(db, user_update.role_name)

        if not new_role:
            raise ValidationError("Specified role was not found")

        # Privilege Escalation Guard 3: Non-admins cannot promote anyone to SYSTEM_ADMIN
        if new_role.name.upper() == "SYSTEM_ADMIN" and not is_admin:
            raise PermissionDeniedError("Only SYSTEM_ADMIN users can grant administrative roles")

        user.role_id = new_role.id

    if user_update.department_id is not None:
        dept_stmt = select(Department).where(Department.id == user_update.department_id)
        dept_res = await db.execute(dept_stmt)
        if not dept_res.scalars().first():
            raise ValidationError("Specified department was not found")
        user.department_id = user_update.department_id

    if user_update.full_name is not None:
        user.full_name = user_update.full_name.strip()
    if user_update.email is not None:
        user.email = user_update.email.strip().lower()
    if user_update.badge_number is not None:
        user.badge_number = user_update.badge_number.strip()
    if user_update.phone_number is not None:
        user.phone_number = user_update.phone_number.strip()
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.metadata is not None:
        user.metadata_ = {**user.metadata_, **user_update.metadata}

    db.add(user)
    await audit_repo.log_action(
        session=db,
        action="UPDATE_USER" if "UPDATE_USER" in audit_repo.__class__.__name__ else "OTHER",
        resource_type="USER",
        resource_id=str(user.id),
        user_id=principal.user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=f"Updated profile for user {user.username}",
    )
    await db.commit()
    await db.refresh(user)

    return ApiResponse(
        success=True,
        data=_to_user_response(user),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{user_id}/reset-password",
    response_model=ApiResponse[Dict[str, str]],
    summary="Reset User Password",
)
async def reset_password(
    user_id: uuid.UUID,
    reset_in: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
) -> ApiResponse[Dict[str, str]]:
    """Reset password for a user. Permitted for administrators, user managers, or the user themselves."""
    is_admin = "SYSTEM_ADMIN" in principal.roles or principal.has_permission("*")
    is_user_manager = is_admin or principal.has_permission("user:manage")
    is_self = principal.user_id == user_id

    if not is_user_manager and not is_self:
        raise PermissionDeniedError("Insufficient permissions to reset password for this user")

    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise NotFoundError(f"User with ID {user_id} not found")

    target_user_is_admin = user.role and user.role.name.upper() == "SYSTEM_ADMIN"
    if target_user_is_admin and not is_admin and not is_self:
        raise PermissionDeniedError("Only SYSTEM_ADMIN users can reset administrator passwords")

    user.password_hash = get_password_hash(reset_in.new_password)
    db.add(user)

    await audit_repo.log_action(
        session=db,
        action="UPDATE_USER" if "UPDATE_USER" in audit_repo.__class__.__name__ else "OTHER",
        resource_type="USER",
        resource_id=str(user.id),
        user_id=principal.user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=f"Password reset for user {user.username}",
    )
    await db.commit()

    return ApiResponse(
        success=True,
        data={"message": f"Password reset successfully for user {user.username}"},
        request_id=getattr(request.state, "request_id", None),
    )
