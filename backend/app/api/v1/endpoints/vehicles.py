from datetime import datetime
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import Principal, require_vehicle_search
from app.db.dependencies import get_db
from app.schemas.analytics import VehicleSearchHit
from app.schemas.common import ApiResponse
from app.schemas.investigation import VehicleMovementHistory, VehicleRouteResponse
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
    "/{vehicle_id}/history",
    response_model=ApiResponse[VehicleMovementHistory],
    summary="Chronological vehicle observation history across cameras",
)
async def get_vehicle_history(
    vehicle_id: uuid.UUID,
    request: Request,
    timestamp_from: Optional[datetime] = Query(None),
    timestamp_to: Optional[datetime] = Query(None),
    district: Optional[str] = Query(None),
    camera_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_vehicle_search),
) -> ApiResponse[VehicleMovementHistory]:
    history = await tracking_service.get_vehicle_history(
        db,
        vehicle_id,
        timestamp_from=timestamp_from,
        timestamp_to=timestamp_to,
        district=district,
        camera_id=camera_id,
        limit=limit,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    return ApiResponse(success=True, data=history, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/{vehicle_id}/route",
    response_model=ApiResponse[VehicleRouteResponse],
    summary="GIS-ready vehicle route data for Leaflet/OpenLayers mapping",
    description="Returns ordered camera sequence points with geographic coordinates, time deltas, and speed telemetry. Explicitly demarcated as OBSERVED_CAMERA_SEQUENCE.",
)
async def get_vehicle_route(
    vehicle_id: uuid.UUID,
    request: Request,
    timestamp_from: Optional[datetime] = Query(None),
    timestamp_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_vehicle_search),
) -> ApiResponse[VehicleRouteResponse]:
    route = await tracking_service.get_vehicle_route(
        db,
        vehicle_id,
        timestamp_from=timestamp_from,
        timestamp_to=timestamp_to,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    return ApiResponse(success=True, data=route, request_id=getattr(request.state, "request_id", None))
