import math
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
from app.schemas.location import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    NearbyLocationResponse,
)
from app.services.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["Locations & GIS"])
location_service = LocationService()


@router.get(
    "/nearby",
    response_model=ApiResponse[List[NearbyLocationResponse]],
    summary="Find Nearby Locations (PostGIS)",
    description="Returns geographic locations within a geodesic radius (meters) using PostGIS ST_DWithin and ST_Distance.",
)
async def get_nearby_locations(
    request: Request,
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Center latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Center longitude in decimal degrees"),
    radius_meters: float = Query(5000.0, gt=0, le=100000.0, description="Search radius in meters (max 100km)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[NearbyLocationResponse]]:
    nearby = await location_service.find_nearby_locations(
        db, latitude=latitude, longitude=longitude, radius_meters=radius_meters, limit=limit
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=nearby, request_id=req_id)


@router.post(
    "",
    response_model=ApiResponse[LocationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Location",
)
async def create_location(
    data: LocationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[LocationResponse]:
    created = await location_service.create_location(db, data)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=LocationResponse.model_validate(created),
        request_id=req_id,
    )


@router.get(
    "",
    response_model=PaginatedResponse[LocationResponse],
    summary="List Locations",
    description="Retrieves a paginated list of geographic locations with district, city and full-text keyword filtering.",
)
async def list_locations(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    district: Optional[str] = Query(None, description="Filter by Gujarat district"),
    city: Optional[str] = Query(None, description="Filter by City"),
    search: Optional[str] = Query(None, description="Search landmark or address"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[LocationResponse]:
    locations, total = await location_service.list_locations(
        db, district=district, city=city, search=search, page=page, page_size=page_size
    )
    req_id = getattr(request.state, "request_id", None)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        success=True,
        data=[LocationResponse.model_validate(l) for l in locations],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
        request_id=req_id,
    )


@router.get(
    "/{location_id}",
    response_model=ApiResponse[LocationResponse],
    summary="Get Location by ID",
)
async def get_location(
    location_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[LocationResponse]:
    loc = await location_service.get_location(db, location_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=LocationResponse.model_validate(loc),
        request_id=req_id,
    )


@router.patch(
    "/{location_id}",
    response_model=ApiResponse[LocationResponse],
    summary="Update Location",
)
async def update_location(
    location_id: uuid.UUID,
    data: LocationUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[LocationResponse]:
    updated = await location_service.update_location(db, location_id, data)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=LocationResponse.model_validate(updated),
        request_id=req_id,
    )


@router.delete(
    "/{location_id}",
    response_model=ApiResponse[dict],
    summary="Delete Location",
)
async def delete_location(
    location_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    await location_service.delete_location(db, location_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data={"message": f"Location {location_id} deleted successfully."},
        request_id=req_id,
    )
