from dataclasses import dataclass
from typing import List, Optional
from fastapi import Depends, Header, Request
import hmac
import uuid

from app.core.config import settings
from app.core.exceptions import AuthenticationError, PermissionDeniedError, ValidationError
from app.core.security import decode_token


@dataclass
class Principal:
    subject: str
    principal_type: str
    roles: List[str]
    user_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None


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
AUDIT_READ_ROLES = {"SYSTEM_ADMIN", "AUDITOR"}


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
) -> Principal:
    expected = settings.AI_WORKER_API_KEY or ""
    if x_phantom_worker_key and expected and hmac.compare_digest(x_phantom_worker_key, expected):
        return Principal(subject="ai-worker", principal_type="worker", roles=["AI_WORKER"])

    token = _extract_bearer(authorization)
    if token and expected and hmac.compare_digest(token, expected):
        return Principal(subject="ai-worker", principal_type="worker", roles=["AI_WORKER"])

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

        return Principal(
            subject=sub,
            principal_type="user",
            roles=[role],
            user_id=uid,
            department_id=dept_id,
        )

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


def _ensure(principal: Principal, allowed: set, message: str) -> Principal:
    if not allowed.intersection(principal.roles):
        raise PermissionDeniedError(message)
    return principal


async def require_ai_ingest(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure(principal, INGEST_ROLES, "AI ingestion is restricted to authorized internal workers")


async def require_detection_read(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure(principal, DETECTION_READ_ROLES, "Insufficient role to read detections")


async def require_vehicle_search(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure(principal, VEHICLE_SEARCH_ROLES, "Insufficient role to search vehicles")


async def require_evidence_access(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure(principal, EVIDENCE_ROLES, "Insufficient role to access evidence metadata")


async def require_watchlist_read(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure(principal, WATCHLIST_READ_ROLES, "Insufficient role to view watchlists")


async def require_watchlist_manage(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure(principal, WATCHLIST_MANAGE_ROLES, "Insufficient role to modify watchlists")


async def require_alert_read(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure(principal, ALERT_READ_ROLES, "Insufficient role to view alerts")


async def require_alert_manage(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure(principal, ALERT_MANAGE_ROLES, "Insufficient role to acknowledge or resolve alerts")


async def require_incident_read(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure(principal, INCIDENT_READ_ROLES, "Insufficient role to view incidents")


async def require_incident_manage(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure(principal, INCIDENT_MANAGE_ROLES, "Insufficient role to manage incidents")


async def require_investigation(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure(principal, INVESTIGATION_ROLES, "Insufficient role to access investigation tools")


async def require_audit_read(principal: Principal = Depends(get_principal)) -> Principal:
    return _ensure(principal, AUDIT_READ_ROLES, "Insufficient role to view audit logs")
