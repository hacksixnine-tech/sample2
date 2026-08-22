from typing import List
import uuid
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.schemas.common import ApiResponse
from app.schemas.stream import (
    CameraStreamCreate,
    CameraStreamUpdate,
    CameraStreamResponse,
)
from app.services.stream_service import StreamService

router = APIRouter(prefix="/cameras/{camera_id}/streams", tags=["Camera Streams & Ingest"])
stream_service = StreamService()


@router.post(
    "",
    response_model=ApiResponse[CameraStreamResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Attach Video Stream to Camera",
)
async def create_camera_stream(
    camera_id: uuid.UUID,
    data: CameraStreamCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CameraStreamResponse]:
    created = await stream_service.create_stream(db, camera_id, data)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=CameraStreamResponse.model_validate(created),
        request_id=req_id,
    )


@router.get(
    "",
    response_model=ApiResponse[List[CameraStreamResponse]],
    summary="List Video Streams for Camera",
)
async def list_camera_streams(
    camera_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[CameraStreamResponse]]:
    streams = await stream_service.list_camera_streams(db, camera_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=[CameraStreamResponse.model_validate(s) for s in streams],
        request_id=req_id,
    )


@router.get(
    "/{stream_id}",
    response_model=ApiResponse[CameraStreamResponse],
    summary="Get Stream Configuration",
)
async def get_stream(
    camera_id: uuid.UUID,
    stream_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CameraStreamResponse]:
    stream = await stream_service.get_stream(db, stream_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=CameraStreamResponse.model_validate(stream),
        request_id=req_id,
    )


@router.patch(
    "/{stream_id}",
    response_model=ApiResponse[CameraStreamResponse],
    summary="Update Stream Parameters",
)
async def update_stream(
    camera_id: uuid.UUID,
    stream_id: uuid.UUID,
    data: CameraStreamUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CameraStreamResponse]:
    updated = await stream_service.update_stream(db, stream_id, data)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=CameraStreamResponse.model_validate(updated),
        request_id=req_id,
    )


@router.delete(
    "/{stream_id}",
    response_model=ApiResponse[dict],
    summary="Detach Video Stream",
)
async def delete_stream(
    camera_id: uuid.UUID,
    stream_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    await stream_service.delete_stream(db, stream_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data={"message": f"Stream {stream_id} deleted successfully."},
        request_id=req_id,
    )
