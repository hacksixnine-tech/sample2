from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Union
import asyncio
import uuid

from app.core.logging import logger
from app.schemas.events import EventEnvelope, EventType


class EventPublisher(ABC):
    """Abstract interface for publishing domain events."""

    @abstractmethod
    async def publish(self, event_name: str, payload: Union[Dict[str, Any], EventEnvelope]) -> None:
        pass


class InMemoryEventPublisher(EventPublisher):
    """
    In-memory and async event bus for real-time WebSocket broadcasting,
    historical replay on reconnection, and telemetry synchronization.
    """

    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[str, List[Callable[[EventEnvelope], Any]]] = {}
        self._event_history: List[EventEnvelope] = []
        self._max_history = max_history

    def subscribe(self, event_name: str, callback: Callable[[EventEnvelope], Any]) -> None:
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[EventEnvelope], Any]) -> None:
        if event_name in self._subscribers and callback in self._subscribers[event_name]:
            self._subscribers[event_name].remove(callback)

    async def publish(
        self,
        event_name: Union[str, EventType],
        payload: Union[Dict[str, Any], EventEnvelope],
        camera_id: Optional[str] = None,
        district: Optional[str] = None,
        severity: Optional[str] = None,
        source: str = "phantom-event-bus",
    ) -> EventEnvelope:
        evt_str = str(event_name.value) if isinstance(event_name, EventType) else str(event_name)

        if isinstance(payload, EventEnvelope):
            envelope = payload
        else:
            # Extract common envelope fields from dict if present
            cid = camera_id or payload.get("camera_id") or payload.get("camera_code")
            dist = district or payload.get("district")
            sev = severity or payload.get("severity")
            eid = payload.get("entity_id") or payload.get("plate_number") or payload.get("normalized_plate")
            etype = payload.get("entity_type") or ("vehicle" if eid else None)

            envelope = EventEnvelope(
                event_id=payload.get("event_id") or str(uuid.uuid4()),
                event_type=evt_str,
                timestamp=datetime.now(timezone.utc).isoformat(),
                source=source,
                camera_id=str(cid) if cid else None,
                district=str(dist) if dist else None,
                severity=str(sev) if sev else None,
                entity_type=str(etype) if etype else None,
                entity_id=str(eid) if eid else None,
                payload=payload,
                created_at=datetime.now(timezone.utc).isoformat(),
            )

        # Store in historical ring buffer for replay
        self._event_history.append(envelope)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        logger.info(
            f"Published real-time event [{envelope.event_type}] id={envelope.event_id} "
            f"cam={envelope.camera_id} sev={envelope.severity}"
        )

        callbacks = self._subscribers.get(evt_str, []) + self._subscribers.get("*", [])
        for cb in callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(envelope)
                else:
                    cb(envelope)
            except Exception as ex:
                logger.error(f"Error in event subscriber for {evt_str}: {ex}")

        return envelope

    def get_history(
        self,
        event_type: Optional[str] = None,
        since_timestamp: Optional[str] = None,
        limit: int = 100,
    ) -> List[EventEnvelope]:
        results = self._event_history

        if event_type and event_type != "*":
            results = [e for e in results if e.event_type == event_type]

        if since_timestamp:
            try:
                since_dt = datetime.fromisoformat(since_timestamp.replace("Z", "+00:00"))
                results = [
                    e for e in results
                    if datetime.fromisoformat(e.timestamp.replace("Z", "+00:00")) >= since_dt
                ]
            except Exception:
                pass

        return list(results[-limit:])


event_publisher = InMemoryEventPublisher()
