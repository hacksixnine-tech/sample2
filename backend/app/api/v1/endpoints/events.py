import asyncio
from datetime import datetime, timezone
import json
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import Principal, get_principal, resolve_principal
from app.core.exceptions import AuthenticationError
from app.core.logging import logger
from app.core.security import decode_token
from app.db.dependencies import get_db
from app.schemas.common import ApiResponse
from app.schemas.events import EventEnvelope, EventSubscription, EventType, HistoricalEventsResponse
from app.services.event_publisher import event_publisher

router = APIRouter(prefix="/events", tags=["Real-Time Event Stream & WebSocket"])


@router.websocket("/ws")
async def unified_events_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT Bearer token or API key for WebSocket authentication"),
):
    """
    Unified Production WebSocket Gateway for PHANTOM Command & Control Center.
    Streams live alerts, ANPR detections, camera telemetry, and system health.
    Supports JWT handshake (?token=...), message-based AUTH frame, Heartbeats (PING/PONG), and category filters.
    """
    await websocket.accept()
    client_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    subscriptions = {"*"}
    authenticated_principal: Optional[Principal] = None

    # Step 1: Query param authentication if token provided during handshake
    if token:
        try:
            authenticated_principal = resolve_principal(query_token=token)
        except Exception as ex:
            await websocket.send_text(
                json.dumps({
                    "type": "AUTH_ERROR",
                    "message": f"Authentication failed: {str(ex)}",
                })
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    def subscriber(envelope: EventEnvelope):
        try:
            evt = envelope.event_type
            if "*" in subscriptions or evt in subscriptions or any(sub in evt for sub in subscriptions):
                queue.put_nowait(envelope)
        except Exception:
            pass

    event_publisher.subscribe("*", subscriber)

    try:
        # Initial greeting & connection handshake
        await websocket.send_text(
            json.dumps({
                "type": "CONNECTION_ESTABLISHED",
                "client_id": client_id,
                "authenticated": authenticated_principal is not None,
                "principal": authenticated_principal.subject if authenticated_principal else None,
                "roles": authenticated_principal.roles if authenticated_principal else [],
                "server_time": datetime.now(timezone.utc).isoformat(),
                "message": "Connected to PHANTOM real-time event pipeline",
            })
        )

        async def listen_incoming():
            """Listen for client authentication frames, heartbeats, and subscription requests."""
            nonlocal authenticated_principal
            while True:
                try:
                    data = await websocket.receive_text()
                    msg = json.loads(data)
                    msg_type = msg.get("type", "").upper()

                    if msg_type == "AUTH":
                        auth_token = msg.get("token")
                        try:
                            authenticated_principal = resolve_principal(query_token=auth_token)
                            await websocket.send_text(
                                json.dumps({
                                    "type": "AUTH_SUCCESS",
                                    "principal": authenticated_principal.subject,
                                    "roles": authenticated_principal.roles,
                                    "permissions": authenticated_principal.permissions,
                                })
                            )
                        except Exception as auth_err:
                            await websocket.send_text(
                                json.dumps({
                                    "type": "AUTH_ERROR",
                                    "message": f"Authentication failed: {str(auth_err)}",
                                })
                            )
                            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                            break
                    elif msg_type == "PING":
                        await websocket.send_text(
                            json.dumps({"type": "PONG", "timestamp": datetime.now(timezone.utc).isoformat()})
                        )
                    elif msg_type == "SUBSCRIBE":
                        cats = msg.get("categories", ["*"])
                        subscriptions.clear()
                        for c in cats:
                            subscriptions.add(c.upper())
                        await websocket.send_text(
                            json.dumps({"type": "SUBSCRIPTION_UPDATED", "active_subscriptions": list(subscriptions)})
                        )
                except (WebSocketDisconnect, json.JSONDecodeError):
                    break
                except Exception as ex:
                    logger.debug(f"WebSocket client message parsing error: {ex}")
                    break

        listen_task = asyncio.create_task(listen_incoming())

        while True:
            try:
                # Wait for next event or send periodic heartbeat ping
                envelope: EventEnvelope = await asyncio.wait_for(queue.get(), timeout=15.0)
                await websocket.send_text(
                    json.dumps({
                        "type": "EVENT",
                        "event_id": envelope.event_id,
                        "event_type": envelope.event_type,
                        "timestamp": envelope.timestamp,
                        "data": envelope.model_dump(),
                    })
                )
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(
                    json.dumps({
                        "type": "HEARTBEAT",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                )

    except (WebSocketDisconnect, Exception):
        pass
    finally:
        event_publisher.unsubscribe("*", subscriber)


@router.get(
    "/history",
    response_model=ApiResponse[HistoricalEventsResponse],
    summary="Get Historical Events for Replay upon Reconnection",
)
async def get_event_history(
    request: Request,
    since: Optional[str] = Query(None, description="ISO timestamp for recovering missed events"),
    event_type: Optional[str] = Query(None, description="Filter by event type or *"),
    limit: int = Query(50, ge=1, le=200),
    principal: Principal = Depends(get_principal),
) -> ApiResponse[HistoricalEventsResponse]:
    events = event_publisher.get_history(event_type=event_type, since_timestamp=since, limit=limit)
    return ApiResponse(
        success=True,
        data=HistoricalEventsResponse(
            total_events=len(events),
            since_timestamp=since,
            events=events,
        ),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/test-event",
    response_model=ApiResponse[EventEnvelope],
    summary="Trigger Development Test Event",
    description="Development endpoint to simulate live Watchlist Match, Camera Offline, or ANPR events.",
)
async def trigger_test_event(
    envelope: EventEnvelope,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> ApiResponse[EventEnvelope]:
    published = await event_publisher.publish(
        event_name=envelope.event_type,
        payload=envelope.payload or {
            "title": f"Test Event: {envelope.event_type}",
            "plate_number": envelope.entity_id or "GJ05AB1234",
            "camera_name": envelope.camera_id or "CAM-014",
            "district": envelope.district or "Surat",
            "severity": envelope.severity or "HIGH",
        },
        camera_id=envelope.camera_id,
        district=envelope.district,
        severity=envelope.severity,
        source="dev-test-generator",
    )
    return ApiResponse(
        success=True,
        data=published,
        request_id=getattr(request.state, "request_id", None),
    )
