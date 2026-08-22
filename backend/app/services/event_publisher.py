from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import asyncio
from app.core.logging import logger


class EventPublisher(ABC):
    """Abstract interface for publishing domain events (e.g. AlertCreatedEvent)."""

    @abstractmethod
    async def publish(self, event_name: str, payload: Dict[str, Any]) -> None:
        pass


class InMemoryEventPublisher(EventPublisher):
    """
    In-memory and async event bus suitable for WebSocket / SSE streaming and local tests.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], Any]]] = {}
        self._event_history: List[Dict[str, Any]] = []

    def subscribe(self, event_name: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)

    async def publish(self, event_name: str, payload: Dict[str, Any]) -> None:
        event_record = {
            "event_name": event_name,
            "payload": payload,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        self._event_history.append(event_record)
        logger.info(f"Published real-time event: {event_name} - {payload.get('alert_code') or payload.get('title')}")

        callbacks = self._subscribers.get(event_name, []) + self._subscribers.get("*", [])
        for cb in callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(payload)
                else:
                    cb(payload)
            except Exception as ex:
                logger.error(f"Error in event subscriber for {event_name}: {ex}")

    def get_history(self, event_name: Optional[str] = None) -> List[Dict[str, Any]]:
        if not event_name:
            return list(self._event_history)
        return [e for e in self._event_history if e["event_name"] == event_name]


event_publisher = InMemoryEventPublisher()
