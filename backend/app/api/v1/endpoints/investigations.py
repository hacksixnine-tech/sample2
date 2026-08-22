from datetime import datetime
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import Principal, require_investigation
from app.db.dependencies import get_db
from app.schemas.common import ApiResponse
from app.schemas.investigation import (
    InvestigationSearchResult,
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
    "/vehicle/{vehicle_id}",
    response_model=ApiResponse[VehicleInvestigationDossier],
    summary="Entity Investigation Summary",
    description="Retrieves the consolidated investigation dossier for a vehicle entity.",
)
async def get_vehicle_investigation_dossier(
    vehicle_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_investigation),
) -> ApiResponse[VehicleInvestigationDossier]:
    dossier = await service.get_vehicle_dossier(
        db, vehicle_id, user_id=principal.user_id, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=dossier,
        request_id=req_id,
    )


@router.get(
    "/vehicle/{vehicle_id}/timeline",
    response_model=ApiResponse[InvestigationTimelineResponse],
    summary="Vehicle Forensic Timeline",
    description="Chronologically combines detections, ANPR reads, watchlist matches, alerts, and incident associations.",
)
async def get_vehicle_investigation_timeline(
    vehicle_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_investigation),
) -> ApiResponse[InvestigationTimelineResponse]:
    timeline = await service.get_vehicle_timeline(
        db, vehicle_id, user_id=principal.user_id, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=timeline,
        request_id=req_id,
    )
