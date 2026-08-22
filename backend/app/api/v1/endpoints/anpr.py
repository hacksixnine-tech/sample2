import math
from datetime import datetime
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import Principal, require_ai_ingest, require_vehicle_search
from app.db.dependencies import get_db
from app.schemas.analytics import ANPRObservationCreate, ANPRObservationResponse
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
from app.services.analytics_service import AnalyticsIngestionService

router = APIRouter(prefix="/anpr", tags=["ANPR Observations"])
service = AnalyticsIngestionService()


def _client_meta(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.post(
    "/observations",
    response_model=ApiResponse[ANPRObservationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest an ANPR observation",
)
async def create_anpr_observation(
    payload: ANPRObservationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_ai_ingest),
) -> ApiResponse[ANPRObservationResponse]:
    obs = await service.ingest_anpr_observation(
        db, payload, actor=principal.subject, user_id=principal.user_id, **_client_meta(request)
    )
    return ApiResponse(
        success=True,
        data=ANPRObservationResponse.model_validate(obs),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/observations",
    response_model=PaginatedResponse[ANPRObservationResponse],
    summary="Search ANPR observations",
)
async def list_anpr_observations(
    request: Request,
    plate: Optional[str] = Query(None),
    camera_id: Optional[uuid.UUID] = Query(None),
    district: Optional[str] = Query(None),
    timestamp_from: Optional[datetime] = Query(None),
    timestamp_to: Optional[datetime] = Query(None),
    confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum plate confidence"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_vehicle_search),
) -> PaginatedResponse[ANPRObservationResponse]:
    from app.ai.anpr.normalize import normalize_plate_text

    rows, total = await service.observations.list_filtered(
        db,
        plate=normalize_plate_text(plate) if plate else None,
        camera_id=camera_id,
        district=district,
        timestamp_from=timestamp_from,
        timestamp_to=timestamp_to,
        confidence_min=confidence,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse(
        success=True,
        data=[ANPRObservationResponse.model_validate(r) for r in rows],
        pagination=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/observations/{observation_id}",
    response_model=ApiResponse[ANPRObservationResponse],
    summary="Get ANPR observation by ID",
)
async def get_anpr_observation(
    observation_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_vehicle_search),
) -> ApiResponse[ANPRObservationResponse]:
    from app.core.exceptions import NotFoundError

    obs = await service.observations.get_by_id(db, observation_id)
    if not obs:
        raise NotFoundError(f"ANPR observation {observation_id} was not found")
    return ApiResponse(
        success=True,
        data=ANPRObservationResponse.model_validate(obs),
        request_id=getattr(request.state, "request_id", None),
    )
