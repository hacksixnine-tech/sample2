from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from app.models.user import User
from app.repositories.base import BaseRepository

VALID_AUDIT_ACTIONS: Set[str] = {
    "LOGIN",
    "LOGOUT",
    "VIEW_ENTITY",
    "VIEW_EVIDENCE",
    "SEARCH_VEHICLE",
    "CREATE_ALERT",
    "ACKNOWLEDGE_ALERT",
    "RESOLVE_ALERT",
    "UPDATE_WATCHLIST",
    "CREATE_CAMERA",
    "UPDATE_CAMERA",
    "DELETE_CAMERA",
    "CREATE_INCIDENT",
    "UPDATE_INCIDENT",
    "EXPORT_DATA",
    "SECURITY_VIOLATION",
    "OTHER",
}


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self):
        super().__init__(AuditLog)

    async def log_action(
        self,
        session: AsyncSession,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        # Normalize action against database CHECK constraint
        safe_action = action.upper()
        meta = metadata or {}
        if safe_action not in VALID_AUDIT_ACTIONS:
            meta["custom_action"] = safe_action
            safe_action = "OTHER"

        valid_user_id: Optional[uuid.UUID] = None
        if user_id:
            try:
                user_exists = await session.scalar(
                    select(func.count()).select_from(User).where(User.id == user_id)
                )
                if user_exists and user_exists > 0:
                    valid_user_id = user_id
                else:
                    meta["caller_user_id"] = str(user_id)
            except Exception:
                meta["caller_user_id"] = str(user_id)

        log_entry = AuditLog(
            user_id=valid_user_id,
            action=safe_action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            metadata_=meta,
        )
        session.add(log_entry)
        await session.flush()
        return log_entry

    async def list_logs(
        self,
        session: AsyncSession,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[AuditLog], int]:
        stmt = select(AuditLog)
        count_stmt = select(func.count()).select_from(AuditLog)

        if action:
            stmt = stmt.where(func.upper(AuditLog.action) == action.upper().strip())
            count_stmt = count_stmt.where(func.upper(AuditLog.action) == action.upper().strip())

        if resource_type:
            stmt = stmt.where(func.upper(AuditLog.resource_type) == resource_type.upper().strip())
            count_stmt = count_stmt.where(func.upper(AuditLog.resource_type) == resource_type.upper().strip())

        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
            count_stmt = count_stmt.where(AuditLog.user_id == user_id)

        if ip_address:
            stmt = stmt.where(AuditLog.ip_address == ip_address.strip())
            count_stmt = count_stmt.where(AuditLog.ip_address == ip_address.strip())

        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
            count_stmt = count_stmt.where(AuditLog.created_at >= start_date)

        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)
            count_stmt = count_stmt.where(AuditLog.created_at <= end_date)

        if search:
            pattern = f"%{search.strip()}%"
            filter_cond = or_(
                AuditLog.details.ilike(pattern),
                AuditLog.resource_id.ilike(pattern),
                AuditLog.resource_type.ilike(pattern),
            )
            stmt = stmt.where(filter_cond)
            count_stmt = count_stmt.where(filter_cond)

        total = await session.scalar(count_stmt) or 0
        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all()), total


audit_repo = AuditRepository()
