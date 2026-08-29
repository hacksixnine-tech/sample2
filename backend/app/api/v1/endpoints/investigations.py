from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import Principal, require_evidence_export, require_investigation
from app.core.exceptions import NotFoundError
from app.db.dependencies import get_db
from app.schemas.common import ApiResponse
from app.schemas.incident import IncidentResponse
from app.schemas.investigation import (
    CameraInvestigationContext,
    DetectionClassificationRequest,
    DetectionClassificationResponse,
    DistrictInvestigationContext,
    ForensicReportResponse,
    InvestigationNoteCreate,
    InvestigationSearchResult,
    InvestigationStatusUpdate,
    InvestigationTimelineResponse,
    VehicleInvestigationDossier,
)
from app.services.investigation_service import InvestigationService

router = APIRouter(prefix="/investigations", tags=["Unified Investigation Intelligence"])
service = InvestigationService()


def _client_meta(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.get(
    "/search",
    response_model=ApiResponse[InvestigationSearchResult],
    summary="Multi-source Investigation Search",
    description="Searches across vehicles, observations, alerts, and incidents using license plate, camera, district, or codes.",
)
async def search_investigations(
    request: Request,
    plate: Optional[str] = Query(None, examples=["GJ01AB1234"], description="License plate number"),
    camera_id: Optional[uuid.UUID] = Query(None, description="Camera UUID"),
    district: Optional[str] = Query(None, examples=["Ahmedabad"], description="District name"),
    alert_code: Optional[str] = Query(None, description="Alert code filter"),
    incident_code: Optional[str] = Query(None, description="Incident code filter"),
    timestamp_from: Optional[datetime] = Query(None, description="Start timestamp"),
    timestamp_to: Optional[datetime] = Query(None, description="End timestamp"),
    limit: int = Query(50, ge=1, le=200, description="Max results per category"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_investigation),
) -> ApiResponse[InvestigationSearchResult]:
    res = await service.search(
        db,
        plate=plate,
        camera_id=camera_id,
        district=district,
        alert_code=alert_code,
        incident_code=incident_code,
        timestamp_from=timestamp_from,
        timestamp_to=timestamp_to,
        limit=limit,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=res,
        request_id=req_id,
    )


@router.get(
    "/vehicle/{identifier}",
    response_model=ApiResponse[VehicleInvestigationDossier],
    summary="Entity Investigation Summary",
    description="Retrieves the consolidated investigation dossier for a vehicle entity by plate or UUID.",
)
async def get_vehicle_investigation_dossier(
    identifier: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_investigation),
) -> ApiResponse[VehicleInvestigationDossier]:
    dossier = await service.get_vehicle_dossier(
        db, identifier, user_id=principal.user_id, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=dossier,
        request_id=req_id,
    )


@router.get(
    "/vehicle/{identifier}/timeline",
    response_model=ApiResponse[InvestigationTimelineResponse],
    summary="Vehicle Forensic Timeline",
    description="Chronologically combines detections, ANPR reads, watchlist matches, alerts, and incident associations.",
)
async def get_vehicle_investigation_timeline(
    identifier: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_investigation),
) -> ApiResponse[InvestigationTimelineResponse]:
    timeline = await service.get_vehicle_timeline(
        db, identifier, user_id=principal.user_id, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=timeline,
        request_id=req_id,
    )


@router.get(
    "/vehicle/{identifier}/report",
    response_model=ApiResponse[ForensicReportResponse],
    summary="Generate Certified Forensic Investigation Report",
    description="Compiles complete vehicle dossier, sightings timeline, GIS route points, evidence SHA-256 digests, and a cryptographic report seal.",
)
async def get_vehicle_forensic_report(
    identifier: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_evidence_export),
) -> ApiResponse[ForensicReportResponse]:
    report = await service.generate_forensic_report(
        db, identifier, user_id=principal.user_id, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=report,
        request_id=req_id,
    )


@router.get(
    "/camera/{camera_id}",
    response_model=ApiResponse[CameraInvestigationContext],
    summary="Camera Forensic Context",
    description="Retrieves camera-centric forensic context including recent sightings, alerts, and coordinates.",
)
async def get_camera_forensic_context(
    camera_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_investigation),
) -> ApiResponse[CameraInvestigationContext]:
    ctx = await service.get_camera_investigation_context(
        db, camera_id, user_id=principal.user_id, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=ctx,
        request_id=req_id,
    )


@router.get(
    "/district/{district}",
    response_model=ApiResponse[DistrictInvestigationContext],
    summary="District Forensic Intelligence Overview",
    description="Retrieves district forensic summary including camera density, sightings, and active alerts.",
)
async def get_district_forensic_context(
    district: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_investigation),
) -> ApiResponse[DistrictInvestigationContext]:
    ctx = await service.get_district_investigation_context(
        db, district, user_id=principal.user_id, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=ctx,
        request_id=req_id,
    )


@router.post(
    "/detections/{detection_id}/classify",
    response_model=ApiResponse[DetectionClassificationResponse],
    summary="Classify Detection (False-Positive Workflow)",
    description="Allows investigators to label detections: CONFIRMED, FALSE_POSITIVE, NEEDS_REVIEW without mutating raw detection attributes.",
)
async def classify_detection(
    detection_id: uuid.UUID,
    payload: DetectionClassificationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_investigation),
) -> ApiResponse[DetectionClassificationResponse]:
    res = await service.classify_detection(
        db,
        detection_id,
        classification=payload.classification,
        notes=payload.notes,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=res,
        request_id=req_id,
    )


@router.get(
    "/{investigation_id}",
    response_model=ApiResponse[IncidentResponse],
    summary="Get Investigation Detail by Incident UUID",
)
async def get_investigation_by_id(
    investigation_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_investigation),
) -> ApiResponse[IncidentResponse]:
    inc = await service.incidents.get_by_id(db, investigation_id)
    if not inc:
        raise NotFoundError(f"Investigation {investigation_id} not found")
    return ApiResponse(
        success=True,
        data=IncidentResponse.model_validate(inc),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{investigation_id}/notes",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Add Investigative Note",
    description="Attaches an authenticated investigator note to the incident dossier.",
)
async def add_investigation_note(
    investigation_id: uuid.UUID,
    payload: InvestigationNoteCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_investigation),
) -> ApiResponse[Dict[str, Any]]:
    note = await service.add_investigation_note(
        db,
        investigation_id,
        note_text=payload.note,
        category=payload.category or "OBSERVATION",
        user_id=principal.user_id,
        **_client_meta(request),
    )
    return ApiResponse(
        success=True,
        data=note,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/{investigation_id}/status",
    response_model=ApiResponse[IncidentResponse],
    summary="Update Investigation Status Lifecycle",
    description="Transitions investigation state: OPEN, UNDER_REVIEW, WATCH, RESOLVED, ARCHIVED.",
)
async def update_investigation_status(
    investigation_id: uuid.UUID,
    payload: InvestigationStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_investigation),
) -> ApiResponse[IncidentResponse]:
    updated = await service.update_investigation_status(
        db,
        investigation_id,
        new_status=payload.status,
        reason=payload.reason,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    return ApiResponse(
        success=True,
        data=IncidentResponse.model_validate(updated),
        request_id=getattr(request.state, "request_id", None),
    )


from pydantic import BaseModel, Field
from app.ai.agents import get_global_copilot_agent, CopilotInvestigationResponse

class CopilotQueryRequest(BaseModel):
    query: str = Field(..., example="Find the red Swift involved in the robbery near Ahmedabad between 8 PM and 10 PM")


@router.post(
    "/copilot/query",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Police Copilot AI Natural Language Investigation",
    description="Translates officer queries into structured tools (Plate, Vehicle, GIS, Evidence) and returns evidence-backed findings.",
)
async def query_police_copilot(
    payload: CopilotQueryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_investigation),
) -> ApiResponse[Dict[str, Any]]:
    agent = get_global_copilot_agent()
    result = await agent.investigate(db, query=payload.query, officer_id=str(principal.user_id))
    return ApiResponse(
        success=True,
        data=result.__dict__,
        request_id=getattr(request.state, "request_id", None),
    )

