import math
from datetime import datetime
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import Principal, require_vehicle_search
from app.db.dependencies import get_db
from app.schemas.analytics import ANPRObservationResponse
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
from app.services.analytics_service import AnalyticsIngestionService
from app.ai.anpr.normalize import normalize_plate_text
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/sightings", tags=["Vehicle Sightings Intelligence"])
service = AnalyticsIngestionService()


def _to_sighting_response(r) -> ANPRObservationResponse:
    cam = getattr(r, "camera", None)
    loc = getattr(r, "location", None) or (getattr(cam, "location", None) if cam else None)
    veh = getattr(r, "vehicle", None)

    cam_name = cam.name if cam else None
    district = loc.district if loc else None
    lat = float(loc.latitude) if loc and getattr(loc, "latitude", None) is not None else None
    lon = float(loc.longitude) if loc and getattr(loc, "longitude", None) is not None else None

    meta = r.metadata_ or {}
    matched_wl = bool(meta.get("matched_watchlist") or meta.get("watchlist_hit"))
    wl_type = meta.get("watchlist_category") or meta.get("watchlist_type")

    veh_type = getattr(veh, "vehicle_type", None) or meta.get("vehicle_type")
    veh_color = getattr(veh, "color", None) or meta.get("color")
    veh_make = getattr(veh, "make", None) or meta.get("make")

    conf = float(r.plate_confidence) if r.plate_confidence is not None else 0.0

    return ANPRObservationResponse(
        id=r.id,
        vehicle_id=r.vehicle_id,
        camera_id=r.camera_id,
        location_id=r.location_id,
        observed_at=r.observed_at,
        raw_plate=r.raw_plate,
        normalized_plate=r.normalized_plate,
        plate_confidence=r.plate_confidence,
        vehicle_confidence=r.vehicle_confidence,
        frame_reference=r.frame_reference,
        detection_reference=r.detection_reference,
        inference_event_id=r.inference_event_id,
        is_demo=r.is_demo,
        anpr_claimed=r.anpr_claimed,
        metadata_=r.metadata_ or {},
        plate_number=r.normalized_plate or r.raw_plate or "",
        raw_plate_text=r.raw_plate or r.normalized_plate or "",
        confidence=conf,
        vehicle_type=veh_type,
        vehicle_color=veh_color,
        vehicle_make=veh_make,
        camera_name=cam_name,
        district=district,
        latitude=lat,
        longitude=lon,
        speed_kmh=float(meta.get("speed_kmh", 0.0)) if meta.get("speed_kmh") else None,
        matched_watchlist=matched_wl,
        watchlist_type=wl_type,
        snapshot_url=r.frame_reference,
    )


@router.get(
    "",
    response_model=PaginatedResponse[ANPRObservationResponse],
    summary="List and Filter Vehicle Sightings",
)
async def list_sightings(
    request: Request,
    plate: Optional[str] = Query(None, description="License plate number"),
    camera_id: Optional[uuid.UUID] = Query(None, description="Camera UUID"),
    district: Optional[str] = Query(None, description="District name"),
    timestamp_from: Optional[datetime] = Query(None, description="Start timestamp"),
    timestamp_to: Optional[datetime] = Query(None, description="End timestamp"),
    watchlist_only: Optional[bool] = Query(False, description="Filter for watchlist hits only"),
    confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum plate confidence"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    limit: Optional[int] = Query(None, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_vehicle_search),
) -> PaginatedResponse[ANPRObservationResponse]:
    effective_limit = limit if limit is not None else page_size
    norm_plate = normalize_plate_text(plate) if plate else None

    rows, total = await service.observations.list_filtered(
        db,
        plate=norm_plate,
        camera_id=camera_id,
        district=district,
        timestamp_from=timestamp_from,
        timestamp_to=timestamp_to,
        confidence_min=confidence,
        skip=(page - 1) * effective_limit,
        limit=effective_limit,
    )

    sighting_responses = [_to_sighting_response(r) for r in rows]
    if watchlist_only:
        sighting_responses = [r for r in sighting_responses if r.matched_watchlist]
        total = len(sighting_responses)

    total_pages = math.ceil(total / effective_limit) if total > 0 else 1
    return PaginatedResponse(
        success=True,
        data=sighting_responses,
        pagination=PaginationMeta(page=page, page_size=effective_limit, total=total, total_pages=total_pages),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/{sighting_id}",
    response_model=ApiResponse[ANPRObservationResponse],
    summary="Get Sighting Detail by ID",
)
async def get_sighting_by_id(
    sighting_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_vehicle_search),
) -> ApiResponse[ANPRObservationResponse]:
    obs = await service.observations.get_by_id(db, sighting_id)
    if not obs:
        raise NotFoundError(f"Vehicle sighting {sighting_id} was not found")
    return ApiResponse(
        success=True,
        data=_to_sighting_response(obs),
        request_id=getattr(request.state, "request_id", None),
    )
