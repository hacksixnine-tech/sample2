from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.schemas.common import ApiResponse
from app.schemas.camera import CameraNearbyResponse, CameraCoverageResponse
from app.schemas.location import NearbyLocationResponse
from app.services.camera_service import CameraService
from app.services.location_service import LocationService

router = APIRouter(prefix="/gis", tags=["GIS & Spatial Intelligence"])
camera_service = CameraService()
location_service = LocationService()


@router.get(
    "/cameras/nearby",
    response_model=ApiResponse[List[CameraNearbyResponse]],
    summary="GIS Nearby Cameras Query",
)
async def gis_nearby_cameras(
    request: Request,
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius_meters: float = Query(5000.0, gt=0, le=100000.0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[CameraNearbyResponse]]:
    nearby = await camera_service.find_nearby_cameras(
        db, latitude=latitude, longitude=longitude, radius_meters=radius_meters, limit=limit
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=nearby, request_id=req_id)


@router.get(
    "/locations/nearby",
    response_model=ApiResponse[List[NearbyLocationResponse]],
    summary="GIS Nearby Locations Query",
)
async def gis_nearby_locations(
    request: Request,
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius_meters: float = Query(5000.0, gt=0, le=100000.0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[NearbyLocationResponse]]:
    nearby = await location_service.find_nearby_locations(
        db, latitude=latitude, longitude=longitude, radius_meters=radius_meters, limit=limit
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=nearby, request_id=req_id)


@router.get(
    "/coverage",
    response_model=ApiResponse[CameraCoverageResponse],
    summary="GIS Statewide Camera Coverage & Density Map",
)
async def gis_coverage(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CameraCoverageResponse]:
    coverage = await camera_service.get_coverage_metrics(db)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=coverage, request_id=req_id)


@router.get(
    "/bbox",
    response_model=ApiResponse[List[dict]],
    summary="GIS Viewport Bounding Box Query",
)
async def gis_bbox(
    request: Request,
    min_lat: float = Query(..., ge=-90.0, le=90.0),
    min_lon: float = Query(..., ge=-180.0, le=180.0),
    max_lat: float = Query(..., ge=-90.0, le=90.0),
    max_lon: float = Query(..., ge=-180.0, le=180.0),
    district: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[dict]]:
    cameras = await camera_service.find_cameras_in_bbox(
        db,
        min_lat=min_lat,
        min_lon=min_lon,
        max_lat=max_lat,
        max_lon=max_lon,
        district=district,
        status=status,
        limit=limit,
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=cameras, request_id=req_id)


@router.get(
    "/corridor",
    response_model=ApiResponse[List[dict]],
    summary="GIS Route Corridor Query",
)
async def gis_corridor(
    request: Request,
    start_lat: float = Query(..., ge=-90.0, le=90.0),
    start_lon: float = Query(..., ge=-180.0, le=180.0),
    end_lat: float = Query(..., ge=-90.0, le=90.0),
    end_lon: float = Query(..., ge=-180.0, le=180.0),
    buffer_meters: float = Query(1000.0, gt=0, le=50000.0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[dict]]:
    cameras = await camera_service.find_cameras_in_corridor(
        db,
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
        buffer_meters=buffer_meters,
        limit=limit,
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=cameras, request_id=req_id)


@router.get(
    "/gaps",
    response_model=ApiResponse[dict],
    summary="GIS Surveillance Gaps Analysis",
)
async def gis_gaps(
    request: Request,
    district: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    analysis = await camera_service.analyze_coverage_gaps(db, district=district)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=analysis, request_id=req_id)

