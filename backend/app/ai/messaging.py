from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable, Deque, Dict, Optional
import time

from app.ai.metrics import metrics


class AIResultPublisher(ABC):
    """Future Kafka / RabbitMQ / Redis Streams implementations plug in here."""

    @abstractmethod
    async def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        ...


class AIResultConsumer(ABC):
    @abstractmethod
    async def consume(self, handler: Callable) -> None:
        ...


class InProcessAIBus(AIResultPublisher, AIResultConsumer):
    """Development/test bus. Does not force Kafka onto every API call."""

    def __init__(self):
        self._queue: Deque[Dict[str, Any]] = deque()
        self._handlers = []

    async def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        envelope = {
            "topic": topic,
            "payload": payload,
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
            "enqueued_monotonic": time.perf_counter(),
        }
        self._queue.append(envelope)
        for handler in list(self._handlers):
            started = envelope["enqueued_monotonic"]
            metrics.observe_queue_ms((time.perf_counter() - started) * 1000.0)
            await handler(topic, payload)

    async def consume(self, handler: Callable) -> None:
        self._handlers.append(handler)

    def drain(self) -> list:
        items = list(self._queue)
        self._queue.clear()
        return items


in_process_bus = InProcessAIBus()
