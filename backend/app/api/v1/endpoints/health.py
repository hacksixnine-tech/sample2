from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.dependencies import get_db
from app.schemas.common import ApiResponse
from app.schemas.health import (
    CameraHealthCreate,
    CameraHealthResponse,
    CameraHealthSummaryResponse,
)
from app.services.health_aggregation import (
    central_health_service,
    regional_health_agent,
)
from app.services.health_service import CameraHealthService
from app.services.stream_gateway_service import stream_gateway_service

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
    "/cameras/health/scale-status",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Statewide Scale & Hierarchical Regional Health Status",
    description="Returns regional health rollup, active stream sessions, and node topology without central polling bottlenecks.",
)
async def get_scale_status(request: Request) -> ApiResponse[Dict[str, Any]]:
    # Ingest local agent report into central aggregator if local node is active
    local_report = regional_health_agent.generate_aggregated_report()
    central_health_service.ingest_regional_report(local_report)

    rollup = central_health_service.get_statewide_health_rollup()
    scale_data = {
        "node_role": settings.NODE_ROLE,
        "regional_zone": settings.REGIONAL_ZONE,
        "active_stream_sessions": stream_gateway_service.get_active_session_count(),
        "default_stream_profile": settings.STREAM_PROFILE_DEFAULT,
        "edge_buffer_enabled": settings.EDGE_BUFFER_ENABLED,
        "health_rollup": rollup,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return ApiResponse(
        success=True,
        data=scale_data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/cameras/health/metrics",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Operational Performance & Bandwidth Sizing Metrics",
    description="Provides real-time system resource metrics, connection pool stats, and mathematical bandwidth estimates across scales.",
)
async def get_operational_metrics(request: Request) -> ApiResponse[Dict[str, Any]]:
    # Calculate mathematical bandwidth requirements across deployment stages
    profile_mgr = stream_gateway_service.profile_manager
    bandwidth_matrix = {
        "50_cameras_poc_mbps": profile_mgr.calculate_raw_video_bandwidth_mbps(50, "MEDIUM"),
        "50_cameras_metadata_mbps": profile_mgr.calculate_metadata_bandwidth_mbps(50),
        "500_cameras_pilot_mbps": profile_mgr.calculate_raw_video_bandwidth_mbps(500, "MEDIUM"),
        "500_cameras_metadata_mbps": profile_mgr.calculate_metadata_bandwidth_mbps(500),
        "5000_cameras_regional_mbps": profile_mgr.calculate_raw_video_bandwidth_mbps(5000, "MEDIUM"),
        "5000_cameras_metadata_mbps": profile_mgr.calculate_metadata_bandwidth_mbps(5000),
        "80000_cameras_statewide_raw_mbps": profile_mgr.calculate_raw_video_bandwidth_mbps(80000, "MEDIUM"),
        "80000_cameras_statewide_metadata_mbps": profile_mgr.calculate_metadata_bandwidth_mbps(80000),
    }

    metrics_data = {
        "server_time": datetime.now(timezone.utc).isoformat(),
        "database_pool": {
            "configured_pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "timeout_seconds": settings.DB_POOL_TIMEOUT,
            "recycle_seconds": settings.DB_POOL_RECYCLE,
        },
        "stream_profiles": {
            "LOW": f"{settings.STREAM_LOW_RES} @ {settings.STREAM_LOW_FPS}fps ({settings.STREAM_LOW_BITRATE_KBPS} kbps)",
            "MEDIUM": f"{settings.STREAM_MEDIUM_RES} @ {settings.STREAM_MEDIUM_FPS}fps ({settings.STREAM_MEDIUM_BITRATE_KBPS} kbps)",
            "HIGH": f"{settings.STREAM_HIGH_RES} @ {settings.STREAM_HIGH_FPS}fps ({settings.STREAM_HIGH_BITRATE_KBPS} kbps)",
            "BURST": f"{settings.STREAM_BURST_RES} @ {settings.STREAM_BURST_FPS}fps ({settings.STREAM_BURST_BITRATE_KBPS} kbps)",
        },
        "ai_inference_sampling": {
            "frame_interval_fps": settings.AI_FRAME_INTERVAL_FPS,
            "dedupe_window_seconds": settings.AI_DEDUPE_WINDOW_SECONDS,
            "confidence_threshold": settings.AI_CONFIDENCE_THRESHOLD,
        },
        "bandwidth_sizing_models": bandwidth_matrix,
    }
    return ApiResponse(
        success=True,
        data=metrics_data,
        request_id=getattr(request.state, "request_id", None),
    )


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
