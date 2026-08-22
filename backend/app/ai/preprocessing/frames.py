from typing import Any, Optional, Tuple
from datetime import datetime, timezone
import time

from app.ai.interfaces import FramePacket
from app.ai.configuration import ALLOWED_SAMPLE_FPS, load_ai_config
from app.core.exceptions import ValidationError


def nearest_sample_fps(requested: float) -> float:
    return min(ALLOWED_SAMPLE_FPS, key=lambda x: abs(x - requested))


def should_sample_frame(last_kept_at: Optional[datetime], now: datetime, fps: float) -> bool:
    if fps <= 0:
        return False
    if last_kept_at is None:
        return True
    left = last_kept_at if last_kept_at.tzinfo else last_kept_at.replace(tzinfo=timezone.utc)
    right = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    min_interval = 1.0 / fps
    return (right - left).total_seconds() >= min_interval - 1e-6


def preprocess_frame(frame: FramePacket, target_size: Optional[Tuple[int, int]] = None) -> FramePacket:
    """Resize/normalize pixel buffers when an image is attached. Identity if no pixels."""
    if frame.image is None:
        return frame
    try:
        import numpy as np  # type: ignore
    except Exception:
        return frame

    image = frame.image
    if isinstance(image, (bytes, bytearray)):
        decoded = _decode_image_bytes(bytes(image))
        if decoded is None:
            raise ValidationError("unsupported image format")
        image = decoded
        frame.image = image

    try:
        import numpy as np  # noqa: F401

        arr = np.asarray(image)
        if arr.ndim not in (2, 3):
            raise ValidationError("invalid frame: expected HxW or HxWxC array")
        h, w = int(arr.shape[0]), int(arr.shape[1])
        frame.height = h
        frame.width = w
        if target_size:
            tw, th = target_size
            frame.image = _resize(arr, tw, th)
            frame.width, frame.height = tw, th
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(f"invalid frame: {exc}") from exc
    return frame


def _decode_image_bytes(data: bytes):
    try:
        import cv2  # type: ignore
        import numpy as np

        buf = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


def _resize(arr, width: int, height: int):
    try:
        import cv2  # type: ignore

        return cv2.resize(arr, (width, height), interpolation=cv2.INTER_LINEAR)
    except Exception:
        try:
            from PIL import Image  # type: ignore
            import numpy as np

            img = Image.fromarray(arr)
            img = img.resize((width, height))
            return np.asarray(img)
        except Exception:
            return arr


class FrameProcessingWorker:
    """Samples and preprocesses frames, then hands them to an inference engine (compute plane)."""

    def __init__(self, target_fps: Optional[float] = None):
        cfg = load_ai_config()
        self.target_fps = nearest_sample_fps(target_fps if target_fps is not None else cfg.frame_interval_fps)
        self._last_kept: dict = {}

    def accept(self, frame: FramePacket) -> Optional[FramePacket]:
        last = self._last_kept.get(str(frame.camera_id))
        if not should_sample_frame(last, frame.timestamp, self.target_fps):
            return None
        prepared = preprocess_frame(frame)
        prepared.timestamp = prepared.timestamp or datetime.now(timezone.utc)
        self._last_kept[str(frame.camera_id)] = prepared.timestamp
        return prepared
