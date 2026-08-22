import math
from typing import Any, Dict, List, Optional, Union
import uuid
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
from app.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraDetailResponse,
    CameraNearbyResponse,
    CameraCoverageResponse,
    CameraBulkImportResponse,
)
from app.services.camera_service import CameraService
from app.services.bulk_import_service import BulkCameraImportService

router = APIRouter(prefix="/cameras", tags=["CCTV Cameras & Registry"])
camera_service = CameraService()
bulk_import_service = BulkCameraImportService()


@router.get(
    "/nearby",
    response_model=ApiResponse[List[CameraNearbyResponse]],
    summary="Find Nearby CCTV Cameras (GIS Spatial Query)",
    description="Finds all active and operational cameras within a specified radius (meters) using PostGIS spatial indexing.",
)
async def get_nearby_cameras(
    request: Request,
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Center latitude"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Center longitude"),
    radius_meters: float = Query(5000.0, gt=0, le=100000.0, description="Search radius in meters (max 100km)"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[CameraNearbyResponse]]:
    nearby = await camera_service.find_nearby_cameras(
        db, latitude=latitude, longitude=longitude, radius_meters=radius_meters, limit=limit
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=nearby, request_id=req_id)


@router.get(
    "/coverage",
    response_model=ApiResponse[CameraCoverageResponse],
    summary="Statewide Camera Coverage Statistics",
    description="Returns aggregate counts of cameras partitioned by department, district, operational status, and camera type.",
)
async def get_camera_coverage(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CameraCoverageResponse]:
    coverage = await camera_service.get_coverage_metrics(db)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=coverage, request_id=req_id)


@router.get(
    "/search",
    response_model=PaginatedResponse[CameraResponse],
    summary="Unified Camera Registry Search",
    description="Global multi-criteria search by camera code, location, district, department, and model.",
)
async def search_cameras(
    request: Request,
    q: Optional[str] = Query(None, description="Search keyword"),
    district: Optional[str] = Query(None, description="District filter"),
    camera_type: Optional[str] = Query(None, description="Camera type filter (ANPR, PTZ, etc.)"),
    status: Optional[str] = Query(None, description="Operational status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CameraResponse]:
    cameras, total = await camera_service.list_cameras(
        db,
        search=q,
        district=district,
        camera_type=camera_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    req_id = getattr(request.state, "request_id", None)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        success=True,
        data=[CameraResponse.model_validate(c) for c in cameras],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
        request_id=req_id,
    )


@router.post(
    "/bulk-import",
    response_model=ApiResponse[CameraBulkImportResponse],
    summary="Bulk Camera Onboarding",
    description="Onboard cameras in bulk via structured JSON list or CSV data. Returns granular per-row validation reports.",
)
async def bulk_import_cameras(
    request: Request,
    payload: Optional[List[Dict[str, Any]]] = None,
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CameraBulkImportResponse]:
    if file:
        content = (await file.read()).decode("utf-8")
        result = await bulk_import_service.import_from_csv_content(db, content)
    elif payload:
        result = await bulk_import_service.import_rows(db, payload)
    else:
        # Fallback to json body if provided in raw request
        try:
            body = await request.json()
            if isinstance(body, list):
                result = await bulk_import_service.import_rows(db, body)
            elif isinstance(body, dict) and "cameras" in body:
                result = await bulk_import_service.import_rows(db, body["cameras"])
            else:
                result = CameraBulkImportResponse(
                    total_rows=0,
                    successful=0,
                    failed=0,
                    errors=[],
                )
        except Exception:
            result = CameraBulkImportResponse(
                total_rows=0,
                successful=0,
                failed=0,
                errors=[],
            )

    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=result, request_id=req_id)


@router.post(
    "",
    response_model=ApiResponse[CameraResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register Camera",
)
async def create_camera(
    data: CameraCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CameraResponse]:
    created = await camera_service.create_camera(db, data)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=CameraResponse.model_validate(created),
        request_id=req_id,
    )


@router.get(
    "",
    response_model=PaginatedResponse[CameraResponse],
    summary="List Cameras",
    description="Retrieve paginated list of cameras with comprehensive filtering.",
)
async def list_cameras(
    request: Request,
    department_id: Optional[uuid.UUID] = Query(None),
    district: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    camera_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    connectivity_status: Optional[str] = Query(None),
    manufacturer: Optional[str] = Query(None),
    ownership: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    location_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CameraResponse]:
    cameras, total = await camera_service.list_cameras(
        db,
        department_id=department_id,
        district=district,
        city=city,
        camera_type=camera_type,
        status=status,
        connectivity_status=connectivity_status,
        manufacturer=manufacturer,
        ownership=ownership,
        search=search,
        location_id=location_id,
        page=page,
        page_size=page_size,
    )
    req_id = getattr(request.state, "request_id", None)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        success=True,
        data=[CameraResponse.model_validate(c) for c in cameras],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
        request_id=req_id,
    )


@router.get(
    "/{camera_id}",
    response_model=ApiResponse[CameraDetailResponse],
    summary="Get Camera Details",
    description="Returns detailed camera profile including department, location coordinates, active stream configurations, and latest health status.",
)
async def get_camera_detail(
    camera_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CameraDetailResponse]:
    detail = await camera_service.get_camera_detail(db, camera_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=detail, request_id=req_id)


@router.patch(
    "/{camera_id}",
    response_model=ApiResponse[CameraResponse],
    summary="Update Camera",
)
async def update_camera(
    camera_id: uuid.UUID,
    data: CameraUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CameraResponse]:
    updated = await camera_service.update_camera(db, camera_id, data)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=CameraResponse.model_validate(updated),
        request_id=req_id,
    )


@router.delete(
    "/{camera_id}",
    response_model=ApiResponse[dict],
    summary="Decommission Camera",
    description="Soft-decommissions a camera, preserving its historical detection trails and audit relations.",
)
async def delete_camera(
    camera_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    await camera_service.delete_camera(db, camera_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data={"message": f"Camera {camera_id} decommissioned successfully."},
        request_id=req_id,
    )
