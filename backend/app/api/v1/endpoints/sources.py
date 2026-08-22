from typing import Any, Dict, List
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.schemas.common import ApiResponse
from app.schemas.source_system import (
    SourceDiscoveryResponse,
    SourceSyncResponse,
    SourceSystemCreate,
    SourceSystemResponse,
)
from app.services.source_discovery_service import SourceDiscoveryService

router = APIRouter(prefix="/sources", tags=["External CCTV Sources"])
discovery_service = SourceDiscoveryService()


@router.get(
    "",
    response_model=ApiResponse[List[SourceSystemResponse]],
    summary="List External CCTV Source Providers",
    description="Returns all registered external CCTV control room source providers.",
)
async def list_sources(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[SourceSystemResponse]]:
    sources = await discovery_service.list_sources(db)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=[SourceSystemResponse.model_validate(s) for s in sources],
        request_id=req_id,
    )


@router.post(
    "",
    response_model=ApiResponse[SourceSystemResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register External CCTV Source Provider",
)
async def create_source(
    data: SourceSystemCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[SourceSystemResponse]:
    created = await discovery_service.create_source(db, data)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=SourceSystemResponse.model_validate(created),
        request_id=req_id,
    )


@router.get(
    "/{source_id}",
    response_model=ApiResponse[SourceSystemResponse],
    summary="Get Source Provider Details",
)
async def get_source(
    source_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[SourceSystemResponse]:
    source = await discovery_service.get_source(db, source_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=SourceSystemResponse.model_validate(source),
        request_id=req_id,
    )


@router.post(
    "/{source_id}/probe",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Probe External CCTV Source Reachability",
    description="Tests live connectivity and latency against the external CCTV control room platform without altering data.",
)
async def probe_source(
    source_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[Dict[str, Any]]:
    result = await discovery_service.probe_source(db, source_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=result, request_id=req_id)


@router.get(
    "/{source_id}/discover",
    response_model=ApiResponse[SourceDiscoveryResponse],
    summary="Discover Live CCTV Cameras from Source",
    description="Queries the external source catalog and extracts camera metadata, RTSP/WebRTC/HLS endpoints without altering the local database.",
)
async def discover_cameras(
    source_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[SourceDiscoveryResponse]:
    discovery = await discovery_service.discover_cameras(db, source_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=discovery, request_id=req_id)


@router.post(
    "/{source_id}/sync",
    response_model=ApiResponse[SourceSyncResponse],
    summary="Synchronize & Onboard External CCTV Cameras",
    description="Discovers and automatically onboards all available live feeds from the external CCTV source into the PHANTOM Camera Registry and GIS database.",
)
async def sync_source_cameras(
    source_id: uuid.UUID,
    request: Request,
    department_code: str = Query("GUJ-POLICE", description="Department code to attach external cameras to"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[SourceSyncResponse]:
    result = await discovery_service.sync_and_onboard_cameras(
        db, source_id=source_id, default_department_code=department_code
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(success=True, data=result, request_id=req_id)
