from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from fastapi import Depends, Header, Query, Request
import hmac
import uuid

from app.core.config import settings
from app.core.exceptions import AuthenticationError, PermissionDeniedError, ValidationError
from app.core.logging import user_id_ctx_var
from app.core.security import decode_token

# Role Permissions Mapping Matrix
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "SYSTEM_ADMIN": ["*"],
    "POLICE_OFFICER": [
        "camera:view",
        "camera:manage",
        "stream:view",
        "stream:manage",
        "alert:view",
        "alert:manage",
        "watchlist:view",
        "watchlist:manage",
        "vehicle:search",
        "detection:read",
        "incident:read",
        "incident:manage",
        "investigation:read",
        "investigation:manage",
        "evidence:view",
        "evidence:export",
        "gis:view",
    ],
    "INVESTIGATOR": [
        "camera:view",
        "stream:view",
        "alert:view",
        "vehicle:search",
        "detection:read",
        "incident:read",
        "incident:manage",
        "investigation:read",
        "investigation:manage",
        "evidence:view",
        "evidence:export",
        "audit:view",
        "gis:view",
    ],
    "ANALYST": [
        "camera:view",
        "stream:view",
        "alert:view",
        "watchlist:view",
        "vehicle:search",
        "detection:read",
        "gis:view",
        "investigation:read",
    ],
    "VIEWER": [
        "camera:view",
        "stream:view",
        "gis:view",
        "alert:view",
    ],
    "AI_WORKER": [
        "ai:ingest",
        "vehicle:search",
        "detection:read",
        "evidence:view",
    ],
    "AUDITOR": [
        "audit:view",
        "camera:view",
        "detection:read",
        "watchlist:view",
        "alert:view",
        "incident:read",
        "investigation:read",
        "evidence:view",
    ],
    "RTO_OFFICER": [
        "vehicle:search",
        "watchlist:view",
        "watchlist:manage",
        "alert:view",
        "detection:read",
    ],
    "DEPARTMENT_OFFICER": [
        "vehicle:search",
        "watchlist:view",
        "watchlist:manage",
        "alert:view",
        "detection:read",
    ],
}


def get_permissions_for_roles(roles: List[str]) -> List[str]:
    """Resolve distinct permissions assigned to the specified roles."""
    perms: Set[str] = set()
    for role in roles:
        normalized_role = role.upper().strip()
        role_perms = ROLE_PERMISSIONS.get(normalized_role, [])
        if "*" in role_perms:
            return ["*"]
        perms.update(role_perms)
    return sorted(list(perms))


@dataclass
class Principal:
    subject: str
    principal_type: str
    roles: List[str]
    user_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    permissions: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.permissions:
            self.permissions = get_permissions_for_roles(self.roles)

    def has_permission(self, permission: str) -> bool:
        if "*" in self.permissions or "SYSTEM_ADMIN" in self.roles:
            return True
        return permission in self.permissions


# Role Collections for backwards-compatibility
INGEST_ROLES = {"AI_WORKER", "SYSTEM_ADMIN"}
VEHICLE_SEARCH_ROLES = {
    "AI_WORKER",
    "SYSTEM_ADMIN",
    "POLICE_OFFICER",
    "RTO_OFFICER",
    "ANALYST",
    "INVESTIGATOR",
    "DEPARTMENT_OFFICER",
}
EVIDENCE_ROLES = {"AI_WORKER", "SYSTEM_ADMIN", "POLICE_OFFICER", "INVESTIGATOR", "AUDITOR"}
DETECTION_READ_ROLES = VEHICLE_SEARCH_ROLES | {"AUDITOR"}

WATCHLIST_READ_ROLES = {
    "SYSTEM_ADMIN",
    "POLICE_OFFICER",
    "RTO_OFFICER",
    "ANALYST",
    "INVESTIGATOR",
    "DEPARTMENT_OFFICER",
    "AUDITOR",
}
WATCHLIST_MANAGE_ROLES = {
    "SYSTEM_ADMIN",
    "POLICE_OFFICER",
    "RTO_OFFICER",
    "INVESTIGATOR",
    "DEPARTMENT_OFFICER",
}

ALERT_READ_ROLES = {
    "SYSTEM_ADMIN",
    "POLICE_OFFICER",
    "RTO_OFFICER",
    "ANALYST",
    "INVESTIGATOR",
    "DEPARTMENT_OFFICER",
    "AUDITOR",
}
ALERT_MANAGE_ROLES = {
    "SYSTEM_ADMIN",
    "POLICE_OFFICER",
    "INVESTIGATOR",
}

INCIDENT_READ_ROLES = {
    "SYSTEM_ADMIN",
    "POLICE_OFFICER",
    "ANALYST",
    "INVESTIGATOR",
    "AUDITOR",
}
INCIDENT_MANAGE_ROLES = {
    "SYSTEM_ADMIN",
    "POLICE_OFFICER",
    "INVESTIGATOR",
}

INVESTIGATION_ROLES = {
    "SYSTEM_ADMIN",
    "POLICE_OFFICER",
    "ANALYST",
    "INVESTIGATOR",
    "AUDITOR",
}
AUDIT_READ_ROLES = {"SYSTEM_ADMIN", "AUDITOR", "INVESTIGATOR"}
USER_MANAGE_ROLES = {"SYSTEM_ADMIN"}
CAMERA_MANAGE_ROLES = {"SYSTEM_ADMIN", "POLICE_OFFICER"}
EVIDENCE_EXPORT_ROLES = {"SYSTEM_ADMIN", "POLICE_OFFICER", "INVESTIGATOR"}


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def resolve_principal(
    x_phantom_worker_key: Optional[str] = None,
    authorization: Optional[str] = None,
    query_token: Optional[str] = None,
) -> Principal:
    expected = settings.AI_WORKER_API_KEY or ""
    if x_phantom_worker_key and expected and hmac.compare_digest(x_phantom_worker_key, expected):
        p = Principal(
            subject="ai-worker",
            principal_type="worker",
            roles=["AI_WORKER"],
        )
        return p

    token = _extract_bearer(authorization) or query_token
    if token and expected and hmac.compare_digest(token, expected):
        p = Principal(
            subject="ai-worker",
            principal_type="worker",
            roles=["AI_WORKER"],
        )
        return p

    if token:
        try:
            payload = decode_token(token)
        except ValueError as exc:
            raise AuthenticationError(str(exc)) from exc
        if payload.get("type") not in (None, "access"):
            raise AuthenticationError("Invalid token type")

        role = str(payload.get("role") or "VIEWER").upper()
        sub = str(payload.get("sub") or "anonymous")

        uid = None
        try:
            uid = uuid.UUID(sub)
        except Exception:
            uid = None

        dept_id = None
        raw_dept = payload.get("department_id") or payload.get("department")
        if raw_dept:
            try:
                dept_id = uuid.UUID(str(raw_dept))
            except Exception:
                dept_id = None

        principal = Principal(
            subject=sub,
            principal_type="user",
            roles=[role],
            user_id=uid,
            department_id=dept_id,
        )
        if uid:
            user_id_ctx_var.set(str(uid))
        return principal

    raise AuthenticationError("Authentication required")


async def get_principal(
    request: Request,
    x_phantom_worker_key: Optional[str] = Header(None, alias="X-PHANTOM-WORKER-KEY"),
    authorization: Optional[str] = Header(None),
) -> Principal:
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > settings.AI_INGEST_MAX_BYTES:
                raise ValidationError("payload too large")
        except ValueError:
            pass
    return resolve_principal(x_phantom_worker_key, authorization)


def _ensure_role_or_perm(
    principal: Principal, allowed_roles: Set[str], permission: str, message: str
) -> Principal:
    if "SYSTEM_ADMIN" in principal.roles or "*" in principal.permissions:
        return principal
    if allowed_roles.intersection(principal.roles) or principal.has_permission(permission):
        return principal
    raise PermissionDeniedError(message)


# Dependency functions
async def require_system_admin(principal: Principal = Depends(get_principal)) -> Principal:
    if "SYSTEM_ADMIN" not in principal.roles and "*" not in principal.permissions:
        raise PermissionDeniedError("Administrative privileges required")
    return principal


async def require_user_manage(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, USER_MANAGE_ROLES, "user:manage", "Insufficient role to manage users"
    )


async def require_audit_view(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, AUDIT_READ_ROLES, "audit:view", "Insufficient role to view audit logs"
    )


# Alias for backward compatibility
require_audit_read = require_audit_view


async def require_ai_ingest(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, INGEST_ROLES, "ai:ingest", "AI ingestion is restricted to authorized internal workers"
    )


async def require_camera_view(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal,
        {"SYSTEM_ADMIN", "POLICE_OFFICER", "INVESTIGATOR", "ANALYST", "VIEWER", "AUDITOR"},
        "camera:view",
        "Insufficient role to view cameras",
    )


async def require_camera_manage(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, CAMERA_MANAGE_ROLES, "camera:manage", "Insufficient role to configure cameras"
    )


async def require_detection_read(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, DETECTION_READ_ROLES, "detection:read", "Insufficient role to read detections"
    )


async def require_vehicle_search(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, VEHICLE_SEARCH_ROLES, "vehicle:search", "Insufficient role to search vehicles"
    )


async def require_evidence_view(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, EVIDENCE_ROLES, "evidence:view", "Insufficient role to access evidence metadata"
    )


# Alias for backward compatibility
require_evidence_access = require_evidence_view


async def require_evidence_export(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, EVIDENCE_EXPORT_ROLES, "evidence:export", "Insufficient role to export evidence"
    )


async def require_watchlist_read(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, WATCHLIST_READ_ROLES, "watchlist:view", "Insufficient role to view watchlists"
    )


# Alias
require_watchlist_view = require_watchlist_read


async def require_watchlist_manage(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, WATCHLIST_MANAGE_ROLES, "watchlist:manage", "Insufficient role to modify watchlists"
    )


async def require_alert_read(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, ALERT_READ_ROLES, "alert:view", "Insufficient role to view alerts"
    )


# Alias
require_alert_view = require_alert_read


async def require_alert_manage(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, ALERT_MANAGE_ROLES, "alert:manage", "Insufficient role to acknowledge or resolve alerts"
    )


async def require_incident_read(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, INCIDENT_READ_ROLES, "incident:read", "Insufficient role to view incidents"
    )


async def require_incident_manage(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, INCIDENT_MANAGE_ROLES, "incident:manage", "Insufficient role to manage incidents"
    )


async def require_investigation(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure_role_or_perm(
        principal, INVESTIGATION_ROLES, "investigation:read", "Insufficient role to access investigation tools"
    )
