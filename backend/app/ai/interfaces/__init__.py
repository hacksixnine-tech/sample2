from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from datetime import datetime
import uuid


PHANTOM_DETECTION_CLASSES = {
    "PERSON",
    "CAR",
    "TRUCK",
    "BUS",
    "MOTORCYCLE",
    "BICYCLE",
    "OTHER_VEHICLE",
    "LICENSE_PLATE",
}


@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "x_min": self.x1,
            "y_min": self.y1,
            "x_max": self.x2,
            "y_max": self.y2,
        }

    def as_list(self) -> List[float]:
        return [self.x1, self.y1, self.x2, self.y2]


@dataclass
class FramePacket:
    camera_id: uuid.UUID
    timestamp: datetime
    source_camera_id: Optional[str] = None
    source_system_id: Optional[uuid.UUID] = None
    frame_reference: Optional[str] = None
    stream_metadata: Dict[str, Any] = field(default_factory=dict)
    image: Any = None  # numpy array or bytes; optional
    width: Optional[int] = None
    height: Optional[int] = None
    is_demo: bool = False


@dataclass
class PlateOCRResult:
    raw_text: str
    normalized_text: str
    confidence: float


@dataclass
class NormalizedDetection:
    detection_id: str
    camera_id: uuid.UUID
    timestamp: datetime
    object_class: str
    confidence: float
    bounding_box: BoundingBox
    model_name: str
    model_version: str
    frame_reference: Optional[str] = None
    source_camera_id: Optional[str] = None
    source_system_id: Optional[uuid.UUID] = None
    track_id: Optional[int] = None
    speed_estimate_kmph: Optional[float] = None
    direction_heading: Optional[str] = None
    plate: Optional[PlateOCRResult] = None
    plate_bbox: Optional[BoundingBox] = None
    plate_crop_reference: Optional[str] = None
    inference_time_ms: Optional[float] = None
    device: Optional[str] = None
    is_demo: bool = False
    raw_model_class: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceBatchResult:
    camera_id: uuid.UUID
    timestamp: datetime
    model_name: str
    model_version: str
    device: str
    inference_time_ms: float
    detections: List[NormalizedDetection]
    frame_reference: Optional[str] = None
    source_camera_id: Optional[str] = None
    source_system_id: Optional[uuid.UUID] = None
    is_demo: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class InferenceEngine(Protocol):
    def infer(self, frame: FramePacket) -> InferenceBatchResult:
        ...


@runtime_checkable
class DetectionEngine(Protocol):
    def detect(self, frame: FramePacket) -> List[NormalizedDetection]:
        ...


@runtime_checkable
class PlateDetector(Protocol):
    def detect_plates(self, frame: FramePacket, vehicle_boxes: List[BoundingBox]) -> List[NormalizedDetection]:
        ...


@runtime_checkable
class OCRProcessor(Protocol):
    def read_text(self, plate_crop: Any) -> PlateOCRResult:
        ...


@runtime_checkable
class ANPREngine(Protocol):
    def recognize(self, frame: FramePacket) -> List[NormalizedDetection]:
        ...
