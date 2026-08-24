import math
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import (
    Principal,
    require_alert_manage,
    require_alert_read,
)
from app.db.dependencies import get_db
from app.schemas.alert import (
    AlertAcknowledgeRequest,
    AlertCreate,
    AlertDismissRequest,
    AlertResolutionRequest,
    AlertResponse,
    AlertUpdate,
)
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
from app.services.alert_engine import AlertEngine

router = APIRouter(prefix="/alerts", tags=["Real-time Alerts Engine"])
alert_engine = AlertEngine()


def _client_meta(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


def _to_alert_response(alert) -> AlertResponse:
    cam_name = alert.camera.name if alert.camera else None
    district = alert.camera.location.district if alert.camera and alert.camera.location else None
    reason = (alert.metadata_ or {}).get("reason")
    return AlertResponse(
        id=alert.id,
        alert_code=alert.alert_code,
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        status=alert.status,
        camera_id=alert.camera_id,
        camera_name=cam_name,
        district=district,
        entity_id=alert.entity_id,
        source_match_id=alert.source_match_id,
        source_event_id=alert.source_event_id,
        acknowledged_by_user_id=alert.acknowledged_by_user_id,
        acknowledged_at=alert.acknowledged_at,
        resolved_by_user_id=alert.resolved_by_user_id,
        resolved_at=alert.resolved_at,
        resolution_notes=alert.resolution_notes,
        reason=reason,
        metadata_=alert.metadata_ or {},
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


@router.post(
    "",
    response_model=ApiResponse[AlertResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Manual / Policy Alert",
)
async def create_alert(
    data: AlertCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_alert_manage),
) -> ApiResponse[AlertResponse]:
    created = await alert_engine.create_alert(
        db, data, user_id=principal.user_id, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=_to_alert_response(created),
        request_id=req_id,
    )


@router.get(
    "",
    response_model=PaginatedResponse[AlertResponse],
    summary="List Alerts",
)
async def list_alerts(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Status filter: NEW, ACKNOWLEDGED, INVESTIGATING, RESOLVED, DISMISSED"),
    severity: Optional[str] = Query(None, description="Severity filter: LOW, INFO, MEDIUM, HIGH, CRITICAL"),
    camera_id: Optional[uuid.UUID] = Query(None, description="Camera filter"),
    entity_id: Optional[uuid.UUID] = Query(None, description="Entity filter"),
    alert_type: Optional[str] = Query(None, description="Alert type filter"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_alert_read),
) -> PaginatedResponse[AlertResponse]:
    alerts, total = await alert_engine.list_alerts(
        db,
        status=status_filter,
        severity=severity,
        camera_id=camera_id,
        entity_id=entity_id,
        alert_type=alert_type,
        page=page,
        page_size=page_size,
    )
    req_id = getattr(request.state, "request_id", None)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        success=True,
        data=[_to_alert_response(a) for a in alerts],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
        request_id=req_id,
    )


@router.get(
    "/{alert_id}",
    response_model=ApiResponse[AlertResponse],
    summary="Get Alert Details",
)
async def get_alert(
    alert_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_alert_read),
) -> ApiResponse[AlertResponse]:
    alert = await alert_engine.get_alert(db, alert_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=_to_alert_response(alert),
        request_id=req_id,
    )


@router.patch(
    "/{alert_id}",
    response_model=ApiResponse[AlertResponse],
    summary="Update Alert",
)
async def update_alert(
    alert_id: uuid.UUID,
    data: AlertUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_alert_manage),
) -> ApiResponse[AlertResponse]:
    updated = await alert_engine.update_alert(
        db, alert_id, data, user_id=principal.user_id, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=_to_alert_response(updated),
        request_id=req_id,
    )


@router.post(
    "/{alert_id}/acknowledge",
    response_model=ApiResponse[AlertResponse],
    summary="Acknowledge Real-Time Alert",
)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    request: Request,
    data: Optional[AlertAcknowledgeRequest] = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_alert_manage),
) -> ApiResponse[AlertResponse]:
    notes = data.notes if data else None
    acknowledged = await alert_engine.acknowledge_alert(
        db, alert_id, user_id=principal.user_id, notes=notes, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=_to_alert_response(acknowledged),
        request_id=req_id,
    )


@router.post(
    "/{alert_id}/resolve",
    response_model=ApiResponse[AlertResponse],
    summary="Resolve Alert",
)
async def resolve_alert(
    alert_id: uuid.UUID,
    data: AlertResolutionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_alert_manage),
) -> ApiResponse[AlertResponse]:
    resolved = await alert_engine.resolve_alert(
        db,
        alert_id,
        resolution_notes=data.resolution_notes,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=_to_alert_response(resolved),
        request_id=req_id,
    )


@router.post(
    "/{alert_id}/dismiss",
    response_model=ApiResponse[AlertResponse],
    summary="Dismiss Alert",
)
async def dismiss_alert(
    alert_id: uuid.UUID,
    data: AlertDismissRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_alert_manage),
) -> ApiResponse[AlertResponse]:
    dismissed = await alert_engine.dismiss_alert(
        db,
        alert_id,
        dismissal_reason=data.dismissal_reason,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=_to_alert_response(dismissed),
        request_id=req_id,
    )


# -----------------------------------------------------------------------------
# Live Alerts Streaming (WebSocket & SSE)
# -----------------------------------------------------------------------------
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import asyncio
import json
from app.services.event_publisher import event_publisher


@router.websocket("/ws")
async def alerts_websocket_endpoint(websocket: WebSocket):
    """
    Real-Time WebSocket feed for live alert broadcasts.
    Subscribes to EventPublisher ALERT_CREATED and ALERT_UPDATED events.
    """
    await websocket.accept()
    queue = asyncio.Queue()

    def subscriber(payload: dict):
        try:
            queue.put_nowait(payload)
        except Exception:
            pass

    event_publisher.subscribe("ALERT_CREATED", subscriber)
    event_publisher.subscribe("ALERT_UPDATED", subscriber)

    try:
        # Send initial connected greeting
        await websocket.send_text(
            json.dumps({"type": "CONNECTION_ESTABLISHED", "message": "Subscribed to PHANTOM real-time alert feed"})
        )
        while True:
            # Wait for either incoming messages (e.g. heartbeat ping) or published alerts
            try:
                alert_payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                await websocket.send_text(
                    json.dumps({"type": "ALERT_NOTIFICATION", "data": alert_payload})
                )
            except asyncio.TimeoutError:
                # Keep connection alive with heartbeat ping
                await websocket.send_text(json.dumps({"type": "HEARTBEAT", "timestamp": datetime.now().isoformat()}))
    except (WebSocketDisconnect, Exception):
        pass


@router.get(
    "/stream",
    summary="Server-Sent Events (SSE) Live Alert Stream",
    description="Stream real-time alert events using HTTP Server-Sent Events",
)
async def alerts_sse_stream(request: Request):
    """SSE endpoint for live browser subscriptions where WebSockets are unavailable."""
    queue = asyncio.Queue()

    def subscriber(payload: dict):
        try:
            queue.put_nowait(payload)
        except Exception:
            pass

    event_publisher.subscribe("ALERT_CREATED", subscriber)
    event_publisher.subscribe("ALERT_UPDATED", subscriber)

    async def event_generator():
        yield f"event: connected\ndata: {json.dumps({'message': 'Connected to alert stream'})}\n\n"
        while True:
            if await request.is_disconnected():
                break
            try:
                data = await asyncio.wait_for(queue.get(), timeout=20.0)
                yield f"event: alert\ndata: {json.dumps(data)}\n\n"
            except asyncio.TimeoutError:
                yield f": ping {datetime.now().isoformat()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

