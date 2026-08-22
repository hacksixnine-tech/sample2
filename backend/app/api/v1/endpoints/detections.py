import math
from datetime import datetime
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import Principal, require_ai_ingest, require_detection_read
from app.db.dependencies import get_db
from app.schemas.analytics import DetectionCreate, DetectionResponse
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
from app.services.analytics_service import AnalyticsIngestionService
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/detections", tags=["AI Observations & Detections"])
service = AnalyticsIngestionService()


def _client_meta(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.post(
    "",
    response_model=ApiResponse[DetectionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a normalized detection",
    description="Authorized AI workers submit a single normalized detection. Heavy inference is not performed in this handler.",
)
async def create_detection(
    payload: DetectionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_ai_ingest),
) -> ApiResponse[DetectionResponse]:
    det = await service.ingest_detection(
        db, payload, actor=principal.subject, user_id=principal.user_id, **_client_meta(request)
    )
    return ApiResponse(
        success=True,
        data=DetectionResponse.model_validate(det),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "",
    response_model=PaginatedResponse[DetectionResponse],
    summary="List detections",
)
async def list_detections(
    request: Request,
    camera_id: Optional[uuid.UUID] = Query(None),
    detection_type: Optional[str] = Query(None),
    confidence_min: Optional[float] = Query(None, ge=0.0, le=1.0),
    timestamp_from: Optional[datetime] = Query(None),
    timestamp_to: Optional[datetime] = Query(None),
    vehicle_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_detection_read),
) -> PaginatedResponse[DetectionResponse]:
    rows, total = await service.detections.list_filtered(
        db,
        camera_id=camera_id,
        detection_type=detection_type,
        confidence_min=confidence_min,
        timestamp_from=timestamp_from,
        timestamp_to=timestamp_to,
        vehicle_id=vehicle_id,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse(
        success=True,
        data=[DetectionResponse.model_validate(r) for r in rows],
        pagination=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/{detection_id}",
    response_model=ApiResponse[DetectionResponse],
    summary="Get detection by ID",
)
async def get_detection(
    detection_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_detection_read),
) -> ApiResponse[DetectionResponse]:
    det = await service.detections.get_by_id(db, detection_id)
    if not det:
        raise NotFoundError(f"Detection {detection_id} was not found")
    return ApiResponse(
        success=True,
        data=DetectionResponse.model_validate(det),
        request_id=getattr(request.state, "request_id", None),
    )
