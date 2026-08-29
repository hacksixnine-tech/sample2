import math
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.ai.interfaces import BoundingBox, NormalizedDetection
from app.core.logging import logger

try:
    import supervision as sv
    SUPERVISION_AVAILABLE = True
except ImportError:
    SUPERVISION_AVAILABLE = False


@dataclass
class TrackHistoryPoint:
    cx: float
    cy: float
    timestamp: float


def compute_heading(dx: float, dy: float) -> str:
    """Calculate 8-directional compass heading from displacement vector (dx, dy)."""
    dist = math.hypot(dx, dy)
    if dist < 3.0:
        return "STATIONARY"
    # Note: image coordinates (y increases downwards)
    angle = math.degrees(math.atan2(-dy, dx))  # Standard math angle where North is +90 deg
    if angle < 0:
        angle += 360

    # Sectors: 0=East, 45=NE, 90=North, 135=NW, 180=West, 225=SW, 270=South, 315=SE
    if 22.5 <= angle < 67.5:
        return "NORTH_EAST"
    elif 67.5 <= angle < 112.5:
        return "NORTH"
    elif 112.5 <= angle < 157.5:
        return "NORTH_WEST"
    elif 157.5 <= angle < 202.5:
        return "WEST"
    elif 202.5 <= angle < 247.5:
        return "SOUTH_WEST"
    elif 247.5 <= angle < 292.5:
        return "SOUTH"
    elif 292.5 <= angle < 337.5:
        return "SOUTH_EAST"
    else:
        return "EAST"


class CameraByteTracker:
    """ByteTrack tracker for a single camera feed with trajectory and velocity smoothing."""

    def __init__(
        self,
        camera_id: str,
        track_activation_threshold: float = 0.25,
        lost_track_buffer: int = 30,
        minimum_matching_threshold: float = 0.8,
        frame_rate: int = 25,
    ):
        self.camera_id = camera_id
        self.last_seen_time = time.time()
        self.track_history: Dict[int, List[TrackHistoryPoint]] = defaultdict(list)

        if SUPERVISION_AVAILABLE:
            self.tracker = sv.ByteTrack(
                track_activation_threshold=track_activation_threshold,
                lost_track_buffer=lost_track_buffer,
                minimum_matching_threshold=minimum_matching_threshold,
                frame_rate=frame_rate,
            )
        else:
            self.tracker = None

    def update(
        self, detections: List[NormalizedDetection], frame_timestamp: Optional[datetime] = None
    ) -> List[NormalizedDetection]:
        self.last_seen_time = time.time()
        if not detections:
            return []

        if not SUPERVISION_AVAILABLE or self.tracker is None:
            # Fallback simple deterministic track ID for dev/demo mode
            for i, det in enumerate(detections):
                if det.track_id is None:
                    det.track_id = i + 1
                    det.direction_heading = "UNKNOWN"
            return detections

        # Build supervision Detections object
        xyxy_list = []
        conf_list = []
        class_id_list = []
        class_name_map = {}

        # Class to integer ID mapping
        for idx, det in enumerate(detections):
            xyxy_list.append(det.bounding_box.as_list())
            conf_list.append(det.confidence)
            cls_name = det.object_class
            if cls_name not in class_name_map:
                class_name_map[cls_name] = len(class_name_map)
            class_id_list.append(class_name_map[cls_name])

        xyxy = np.array(xyxy_list, dtype=np.float32)
        confidence = np.array(conf_list, dtype=np.float32)
        class_id = np.array(class_id_list, dtype=int)

        sv_detections = sv.Detections(
            xyxy=xyxy,
            confidence=confidence,
            class_id=class_id,
        )

        # Update ByteTrack
        tracked_sv = self.tracker.update_with_detections(sv_detections)

        # Match tracked detections back to NormalizedDetection list
        now_ts = frame_timestamp.timestamp() if frame_timestamp else time.time()
        updated_detections: List[NormalizedDetection] = []

        if len(tracked_sv) > 0 and tracked_sv.tracker_id is not None:
            for i, (box, trk_id, conf) in enumerate(
                zip(tracked_sv.xyxy, tracked_sv.tracker_id, tracked_sv.confidence)
            ):
                t_id = int(trk_id)
                bx = BoundingBox(float(box[0]), float(box[1]), float(box[2]), float(box[3]))
                cx = (bx.x1 + bx.x2) / 2.0
                cy = (bx.y1 + bx.y2) / 2.0

                # Find closest matching original detection
                best_det = None
                best_iou = -1.0
                for orig in detections:
                    iou = _calc_iou(orig.bounding_box, bx)
                    if iou > best_iou:
                        best_iou = iou
                        best_det = orig

                if best_det is None:
                    continue

                best_det.track_id = t_id
                best_det.bounding_box = bx

                # Update trajectory and compute speed/heading
                history = self.track_history[t_id]
                history.append(TrackHistoryPoint(cx=cx, cy=cy, timestamp=now_ts))
                if len(history) > 30:
                    history.pop(0)

                if len(history) >= 2:
                    first = history[0]
                    last = history[-1]
                    dt = last.timestamp - first.timestamp
                    dx = last.cx - first.cx
                    dy = last.cy - first.cy
                    best_det.direction_heading = compute_heading(dx, dy)
                    if dt > 0.001:
                        # Proxy speed estimation (pixels per second to km/h rough estimation factor)
                        pixel_speed = math.hypot(dx, dy) / dt
                        best_det.speed_estimate_kmph = round(min(pixel_speed * 0.15, 160.0), 1)
                    else:
                        best_det.speed_estimate_kmph = 35.0
                
                updated_detections.append(best_det)

        # Include detections that may not have been tracked yet (e.g. initial frame or small objects)
        tracked_objs = {id(d) for d in updated_detections}
        for det in detections:
            if id(det) not in tracked_objs:
                updated_detections.append(det)

        return updated_detections


def _calc_iou(boxA: BoundingBox, boxB: BoundingBox) -> float:
    xA = max(boxA.x1, boxB.x1)
    yA = max(boxA.y1, boxB.y1)
    xB = min(boxA.x2, boxB.x2)
    yB = min(boxA.y2, boxB.y2)

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA.x2 - boxA.x1) * (boxA.y2 - boxA.y1)
    boxBArea = (boxB.x2 - boxB.x1) * (boxB.y2 - boxB.y1)
    denom = float(boxAArea + boxBArea - interArea)
    if denom <= 0:
        return 0.0
    return interArea / denom


class ByteTrackManager:
    """Manages independent ByteTrack instances across multiple camera feeds."""

    def __init__(self, ttl_seconds: float = 300.0):
        self._trackers: Dict[str, CameraByteTracker] = {}
        self.ttl_seconds = ttl_seconds

    def track(
        self,
        camera_id: uuid.UUID,
        detections: List[NormalizedDetection],
        frame_timestamp: Optional[datetime] = None,
    ) -> List[NormalizedDetection]:
        cid_str = str(camera_id)
        self._cleanup_expired()

        if cid_str not in self._trackers:
            self._trackers[cid_str] = CameraByteTracker(camera_id=cid_str)

        tracker = self._trackers[cid_str]
        return tracker.update(detections, frame_timestamp=frame_timestamp)

    def _cleanup_expired(self):
        now = time.time()
        expired = [
            cid
            for cid, trk in self._trackers.items()
            if (now - trk.last_seen_time) > self.ttl_seconds
        ]
        for cid in expired:
            del self._trackers[cid]


_global_tracker = ByteTrackManager()


def get_global_tracker() -> ByteTrackManager:
    return _global_tracker
