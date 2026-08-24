from datetime import datetime
import math
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import Principal, require_audit_view
from app.core.exceptions import NotFoundError
from app.db.dependencies import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.repositories.audit import audit_repo
from app.schemas.audit import AuditLogResponse
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/audit", tags=["Governance & Immutable Audit Trails"])


def _to_audit_response(log: AuditLog, username: Optional[str] = None) -> AuditLogResponse:
    # Username might be embedded in metadata or resolved
    resolved_username = username
    if not resolved_username and log.metadata_:
        resolved_username = log.metadata_.get("username") or log.metadata_.get("caller_user_id")

    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        username=resolved_username,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        details=log.details,
        metadata=log.metadata_,
        created_at=log.created_at,
    )


@router.get(
    "",
    response_model=PaginatedResponse[AuditLogResponse],
    summary="List and Filter Centralized Immutable Audit Logs",
    description="Retrieve tamper-proof audit trails filterable by action, resource type, user, date range, or IP address. Append-only.",
)
async def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    action: Optional[str] = Query(None, description="Filter by action (e.g. LOGIN, LOGOUT, SEARCH_VEHICLE, VIEW_EVIDENCE)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (e.g. AUTH, VEHICLE, CAMERA, ALERT)"),
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user UUID"),
    ip_address: Optional[str] = Query(None, description="Filter by client IP address"),
    start_date: Optional[datetime] = Query(None, description="Filter start datetime (ISO-8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter end datetime (ISO-8601)"),
    search: Optional[str] = Query(None, description="Search details, resource ID, or resource type"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_audit_view),
) -> PaginatedResponse[AuditLogResponse]:
    """Retrieve paginated, filterable immutable audit records."""
    offset = (page - 1) * page_size
    logs, total = await audit_repo.list_logs(
        session=db,
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        ip_address=ip_address,
        start_date=start_date,
        end_date=end_date,
        search=search,
        offset=offset,
        limit=page_size,
    )

    # Collect user IDs to resolve usernames in batch
    user_ids = {l.user_id for l in logs if l.user_id is not None}
    user_map = {}
    if user_ids:
        user_stmt = select(User.id, User.username).where(User.id.in_(user_ids))
        user_res = await db.execute(user_stmt)
        for uid, uname in user_res.all():
            user_map[uid] = uname

    items = [_to_audit_response(l, user_map.get(l.user_id)) for l in logs]
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


@router.get(
    "/{audit_id}",
    response_model=ApiResponse[AuditLogResponse],
    summary="Get Specific Audit Trail Log Details",
    description="Inspect a single immutable audit log record by UUID.",
)
async def get_audit_log(
    audit_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_audit_view),
) -> ApiResponse[AuditLogResponse]:
    """Retrieve detailed information for a single audit event."""
    log = await audit_repo.get_by_id(db, audit_id)
    if not log:
        raise NotFoundError(f"Audit log entry with ID {audit_id} not found")

    username = None
    if log.user_id:
        user_stmt = select(User.username).where(User.id == log.user_id)
        user_res = await db.execute(user_stmt)
        username = user_res.scalars().first()

    return ApiResponse(
        success=True,
        data=_to_audit_response(log, username),
        request_id=getattr(request.state, "request_id", None),
    )
