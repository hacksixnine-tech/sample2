from typing import List
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.schemas.common import ApiResponse
from app.schemas.health import (
    CameraHealthCreate,
    CameraHealthResponse,
    CameraHealthSummaryResponse,
)
from app.services.health_service import CameraHealthService

router = APIRouter(tags=["Camera Health & Observability"])
health_service = CameraHealthService()


@router.get(
    "/cameras/health/summary",
    response_model=ApiResponse[CameraHealthSummaryResponse],
    summary="Real-time Camera Fleet Health Summary",
    description="Returns high-level aggregate health counts (Online, Degraded, Offline, Maintenance) across all statewide cameras.",
)
async def get_camera_health_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CameraHealthSummaryResponse]:
    summary = await health_service.get_summary(db)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=summary, request_id=req_id)


@router.get(
    "/cameras/{camera_id}/health",
    response_model=ApiResponse[CameraHealthResponse],
    summary="Get Latest Camera Health Observation",
)
async def get_camera_health(
    camera_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CameraHealthResponse]:
    health = await health_service.get_latest_health(db, camera_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=CameraHealthResponse.model_validate(health),
        request_id=req_id,
    )


@router.get(
    "/cameras/{camera_id}/health/history",
    response_model=ApiResponse[List[CameraHealthResponse]],
    summary="Get Historical Camera Health Observations",
)
async def get_camera_health_history(
    camera_id: uuid.UUID,
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[CameraHealthResponse]]:
    history = await health_service.get_health_history(db, camera_id, limit=limit)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=[CameraHealthResponse.model_validate(h) for h in history],
        request_id=req_id,
    )


@router.post(
    "/cameras/{camera_id}/health",
    response_model=ApiResponse[CameraHealthResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record Camera Health Heartbeat / Probe Telemetry",
)
async def record_camera_health(
    camera_id: uuid.UUID,
    data: CameraHealthCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CameraHealthResponse]:
    created = await health_service.record_camera_health(db, camera_id, data)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=CameraHealthResponse.model_validate(created),
        request_id=req_id,
    )
