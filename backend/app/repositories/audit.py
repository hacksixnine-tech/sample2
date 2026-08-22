from typing import Any, Dict, Optional, Set
import uuid
from sqlalchemy import select, func
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

