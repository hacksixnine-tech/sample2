from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.core.logging import logger


class NotificationChannel(ABC):
    @abstractmethod
    async def send(self, recipient: str, title: str, message: str, payload: Dict[str, Any]) -> bool:
        pass


class InAppNotificationChannel(NotificationChannel):
    def __init__(self):
        self.sent_notifications: List[Dict[str, Any]] = []

    async def send(self, recipient: str, title: str, message: str, payload: Dict[str, Any]) -> bool:
        record = {
            "channel": "IN_APP",
            "recipient": recipient,
            "title": title,
            "message": message,
            "payload": payload,
        }
        self.sent_notifications.append(record)
        logger.info(f"[InApp Notification] To: {recipient} | {title} | {message}")
        return True


class NotificationService:
    def __init__(self):
        self._channels: Dict[str, NotificationChannel] = {
            "IN_APP": InAppNotificationChannel(),
        }

    def register_channel(self, name: str, channel: NotificationChannel) -> None:
        self._channels[name.upper()] = channel

    async def notify(
        self,
        title: str,
        message: str,
        recipient: str = "broadcast",
        channels: Optional[List[str]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        target_channels = channels or ["IN_APP"]
        results = {}
        data = payload or {}
        for ch_name in target_channels:
            channel = self._channels.get(ch_name.upper())
            if channel:
                results[ch_name] = await channel.send(recipient, title, message, data)
            else:
                logger.warning(f"Notification channel {ch_name} is not configured or disabled.")
                results[ch_name] = False
        return results


notification_service = NotificationService()
