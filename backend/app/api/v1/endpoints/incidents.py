import math
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import (
    Principal,
    require_incident_manage,
    require_incident_read,
)
from app.db.dependencies import get_db
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
    LinkNotesRequest,
    LinkedAlertResponse,
    LinkedEntityResponse,
    LinkedEventResponse,
    LinkedEvidenceResponse,
)
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["Incident Management & Dossiers"])
service = IncidentService()


def _client_meta(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


def _to_incident_response(inc) -> IncidentResponse:
    alerts = []
    if inc.alerts:
        for a in inc.alerts:
            alt = a.alert
            alerts.append(
                LinkedAlertResponse(
                    alert_id=a.alert_id,
                    alert_code=alt.alert_code if alt else None,
                    title=alt.title if alt else None,
                    severity=alt.severity if alt else None,
                    status=alt.status if alt else None,
                    added_at=a.added_at,
                    notes=a.notes,
                )
            )

    events = []
    if inc.events:
        for e in inc.events:
            ev = e.event
            events.append(
                LinkedEventResponse(
                    event_id=e.event_id,
                    event_type=ev.event_type if ev else None,
                    occurred_at=ev.occurred_at if ev else None,
                    added_at=e.added_at,
                    notes=e.notes,
                )
            )

    entities = []
    if inc.entities:
        for ent in inc.entities:
            entity_obj = ent.entity
            entities.append(
                LinkedEntityResponse(
                    entity_id=ent.entity_id,
                    primary_identifier=entity_obj.primary_identifier if entity_obj else None,
                    entity_type=entity_obj.entity_type if entity_obj else None,
                    involvement_role=ent.involvement_role,
                    added_at=ent.added_at,
                    notes=ent.notes,
                )
            )

    evidence_list = []
    if inc.evidence_links:
        for evd in inc.evidence_links:
            ev_obj = evd.evidence
            evidence_list.append(
                LinkedEvidenceResponse(
                    evidence_id=evd.evidence_id,
                    evidence_code=ev_obj.evidence_code if ev_obj else None,
                    evidence_type=ev_obj.evidence_type if ev_obj else None,
                    added_at=evd.added_at,
                    notes=evd.notes,
                )
            )

    return IncidentResponse(
        id=inc.id,
        incident_code=inc.incident_code,
        title=inc.title,
        description=inc.description,
        severity=inc.severity,
        status=inc.status,
        assigned_department_id=inc.assigned_department_id,
        assigned_department_name=inc.assigned_department.name if inc.assigned_department else None,
        assigned_user_id=inc.assigned_user_id,
        assigned_user_name=inc.assigned_user.full_name if inc.assigned_user else None,
        occurred_at=inc.occurred_at,
        closed_at=inc.closed_at,
        closing_notes=inc.closing_notes,
        alerts_count=len(alerts),
        events_count=len(events),
        entities_count=len(entities),
        evidence_count=len(evidence_list),
        alerts=alerts,
        events=events,
        entities=entities,
        evidence=evidence_list,
        metadata_=inc.metadata_ or {},
        created_at=inc.created_at,
        updated_at=inc.updated_at,
    )


@router.post(
    "",
    response_model=ApiResponse[IncidentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Incident Dossier",
)
async def create_incident(
    data: IncidentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_incident_manage),
) -> ApiResponse[IncidentResponse]:
    dept_id = data.assigned_department_id or principal.department_id
    data.assigned_department_id = dept_id
    created = await service.create_incident(
        db, data, user_id=principal.user_id, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=_to_incident_response(created),
        request_id=req_id,
    )


@router.get(
    "",
    response_model=PaginatedResponse[IncidentResponse],
    summary="List Incident Dossiers",
)
async def list_incidents(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Incident status filter"),
    severity: Optional[str] = Query(None, description="Severity filter"),
    department_id: Optional[uuid.UUID] = Query(None, description="Assigned department filter"),
    search: Optional[str] = Query(None, description="Search title, description or code"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_incident_read),
) -> PaginatedResponse[IncidentResponse]:
    incidents, total = await service.list_incidents(
        db,
        status=status_filter,
        severity=severity,
        department_id=department_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    req_id = getattr(request.state, "request_id", None)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        success=True,
        data=[_to_incident_response(i) for i in incidents],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
        request_id=req_id,
    )


@router.get(
    "/{incident_id}",
    response_model=ApiResponse[IncidentResponse],
    summary="Get Incident Dossier Details",
)
async def get_incident(
    incident_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_incident_read),
) -> ApiResponse[IncidentResponse]:
    inc = await service.get_incident(db, incident_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=_to_incident_response(inc),
        request_id=req_id,
    )


@router.patch(
    "/{incident_id}",
    response_model=ApiResponse[IncidentResponse],
    summary="Update Incident Dossier",
)
async def update_incident(
    incident_id: uuid.UUID,
    data: IncidentUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_incident_manage),
) -> ApiResponse[IncidentResponse]:
    updated = await service.update_incident(
        db, incident_id, data, user_id=principal.user_id, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=_to_incident_response(updated),
        request_id=req_id,
    )


@router.post(
    "/{incident_id}/alerts/{alert_id}",
    response_model=ApiResponse[IncidentResponse],
    summary="Link Alert to Incident",
)
async def link_alert_to_incident(
    incident_id: uuid.UUID,
    alert_id: uuid.UUID,
    request: Request,
    data: Optional[LinkNotesRequest] = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_incident_manage),
) -> ApiResponse[IncidentResponse]:
    notes = data.notes if data else None
    updated = await service.link_alert(db, incident_id, alert_id, notes=notes)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=_to_incident_response(updated),
        request_id=req_id,
    )


@router.post(
    "/{incident_id}/events/{event_id}",
    response_model=ApiResponse[IncidentResponse],
    summary="Link Event to Incident",
)
async def link_event_to_incident(
    incident_id: uuid.UUID,
    event_id: uuid.UUID,
    request: Request,
    data: Optional[LinkNotesRequest] = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_incident_manage),
) -> ApiResponse[IncidentResponse]:
    notes = data.notes if data else None
    updated = await service.link_event(db, incident_id, event_id, notes=notes)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=_to_incident_response(updated),
        request_id=req_id,
    )
