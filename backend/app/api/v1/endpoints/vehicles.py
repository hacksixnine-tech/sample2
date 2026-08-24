from datetime import datetime
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import Principal, require_vehicle_search
from app.db.dependencies import get_db
from app.schemas.analytics import VehicleSearchHit
from app.schemas.common import ApiResponse
from app.schemas.investigation import (
    VehicleMovementHistory,
    VehicleRouteResponse,
    VehicleSummaryResponse,
)
from app.services.analytics_service import AnalyticsIngestionService
from app.services.tracking_service import TrackingService

router = APIRouter(prefix="/vehicles", tags=["Vehicle Registry & Search"])
analytics_service = AnalyticsIngestionService()
tracking_service = TrackingService()


def _client_meta(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.get(
    "/search",
    response_model=ApiResponse[List[VehicleSearchHit]],
    summary="Search vehicles by plate, camera, district, and time range",
)
async def search_vehicles(
    request: Request,
    plate: Optional[str] = Query(None, examples=["GJ01TEST001"]),
    camera_id: Optional[uuid.UUID] = Query(None),
    district: Optional[str] = Query(None),
    timestamp_from: Optional[datetime] = Query(None),
    timestamp_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_vehicle_search),
) -> ApiResponse[List[VehicleSearchHit]]:
    hits = await analytics_service.search_vehicles(
        db,
        plate=plate,
        camera_id=camera_id,
        district=district,
        timestamp_from=timestamp_from,
        timestamp_to=timestamp_to,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    return ApiResponse(success=True, data=hits, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/{identifier}",
    response_model=ApiResponse[VehicleSummaryResponse],
    summary="Get Vehicle Profile and Identity Details",
    description="Resolves vehicle profile by license plate string (e.g. GJ05AB1234) or UUID.",
)
async def get_vehicle_profile(
    identifier: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_vehicle_search),
) -> ApiResponse[VehicleSummaryResponse]:
    summary = await tracking_service.get_vehicle_summary(
        db,
        identifier,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    return ApiResponse(success=True, data=summary, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/{identifier}/summary",
    response_model=ApiResponse[VehicleSummaryResponse],
    summary="Get Comprehensive Vehicle Movement Analytics Summary",
)
async def get_vehicle_summary(
    identifier: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_vehicle_search),
) -> ApiResponse[VehicleSummaryResponse]:
    summary = await tracking_service.get_vehicle_summary(
        db,
        identifier,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    return ApiResponse(success=True, data=summary, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/{identifier}/timeline",
    response_model=ApiResponse[VehicleMovementHistory],
    summary="Chronological Vehicle Sightings Timeline with Transition Telemetry",
    description="Supports sorting by order=desc (newest first for live investigation) or order=asc (oldest first for route reconstruction).",
)
@router.get(
    "/{identifier}/history",
    response_model=ApiResponse[VehicleMovementHistory],
    summary="Alias for Vehicle Movement History",
)
async def get_vehicle_timeline(
    identifier: str,
    request: Request,
    timestamp_from: Optional[datetime] = Query(None),
    timestamp_to: Optional[datetime] = Query(None),
    district: Optional[str] = Query(None),
    camera_id: Optional[uuid.UUID] = Query(None),
    watchlist_only: Optional[bool] = Query(False, description="Filter for watchlist hits only"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order: 'desc' (newest first) or 'asc' (oldest first)"),
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_vehicle_search),
) -> ApiResponse[VehicleMovementHistory]:
    history = await tracking_service.get_vehicle_history(
        db,
        identifier,
        timestamp_from=timestamp_from,
        timestamp_to=timestamp_to,
        district=district,
        camera_id=camera_id,
        watchlist_only=watchlist_only,
        sort_order=order,
        limit=limit,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    return ApiResponse(success=True, data=history, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/{identifier}/route",
    response_model=ApiResponse[VehicleRouteResponse],
    summary="GIS-ready Observed Camera Sequence Route",
    description="Returns ordered camera sequence points with geographic coordinates, time deltas, and speed telemetry. Explicitly demarcated as OBSERVED_CAMERA_SEQUENCE.",
)
async def get_vehicle_route(
    identifier: str,
    request: Request,
    timestamp_from: Optional[datetime] = Query(None),
    timestamp_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_vehicle_search),
) -> ApiResponse[VehicleRouteResponse]:
    route = await tracking_service.get_vehicle_route(
        db,
        identifier,
        timestamp_from=timestamp_from,
        timestamp_to=timestamp_to,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    return ApiResponse(success=True, data=route, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/{identifier}/export",
    summary="Export Vehicle Sightings to CSV",
    description="Generates a downloadable CSV containing full forensic sighting and transition records respecting filters.",
)
async def export_vehicle_csv(
    identifier: str,
    request: Request,
    timestamp_from: Optional[datetime] = Query(None),
    timestamp_to: Optional[datetime] = Query(None),
    district: Optional[str] = Query(None),
    camera_id: Optional[uuid.UUID] = Query(None),
    watchlist_only: Optional[bool] = Query(False),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_vehicle_search),
):
    csv_text = await tracking_service.export_vehicle_history_csv(
        db,
        identifier,
        timestamp_from=timestamp_from,
        timestamp_to=timestamp_to,
        district=district,
        camera_id=camera_id,
        watchlist_only=watchlist_only,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    filename = f"phantom_vehicle_{identifier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
