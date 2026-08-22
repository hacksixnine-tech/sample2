from datetime import datetime, timezone
import time
import uuid
from typing import List

from app.ai.configuration import load_ai_config
from app.ai.interfaces import (
    ANPREngine,
    BoundingBox,
    DetectionEngine,
    FramePacket,
    InferenceBatchResult,
    InferenceEngine,
    NormalizedDetection,
    OCRProcessor,
    PlateDetector,
    PlateOCRResult,
)
from app.ai.anpr.normalize import normalize_plate_text
from app.ai.postprocessing.classes import normalize_detection_class
from app.ai.postprocessing.validation import validate_confidence, parse_bbox

DEMO_PLATE_RAW = "GJ 01 TEST 001"
DEMO_PLATE_NORMALIZED = "GJ01TEST001"


class DemoDetectionEngine:
    """Deterministic sample detections. Always marked DEMO. Not live CCTV output."""

    def detect(self, frame: FramePacket) -> List[NormalizedDetection]:
        cfg = load_ai_config()
        ts = frame.timestamp
        vehicle = NormalizedDetection(
            detection_id=str(uuid.uuid4()),
            camera_id=frame.camera_id,
            timestamp=ts,
            object_class="CAR",
            confidence=0.91,
            bounding_box=BoundingBox(80, 120, 420, 380),
            model_name="phantom-demo-detector",
            model_version="demo-1.0.0",
            frame_reference=frame.frame_reference,
            source_camera_id=frame.source_camera_id,
            source_system_id=frame.source_system_id,
            is_demo=True,
            raw_model_class="car",
            metadata={"origin": "DEMO_AI_MODE", "not_live_cctv": True},
        )
        plate = NormalizedDetection(
            detection_id=str(uuid.uuid4()),
            camera_id=frame.camera_id,
            timestamp=ts,
            object_class="LICENSE_PLATE",
            confidence=0.95,
            bounding_box=BoundingBox(140, 300, 300, 340),
            model_name="phantom-demo-detector",
            model_version="demo-1.0.0",
            frame_reference=frame.frame_reference,
            source_camera_id=frame.source_camera_id,
            source_system_id=frame.source_system_id,
            plate=PlateOCRResult(
                raw_text=DEMO_PLATE_RAW,
                normalized_text=DEMO_PLATE_NORMALIZED,
                confidence=0.94,
            ),
            plate_bbox=BoundingBox(140, 300, 300, 340),
            plate_crop_reference=None,
            is_demo=True,
            raw_model_class="license_plate",
            metadata={"origin": "DEMO_AI_MODE", "not_live_cctv": True},
        )
        return [vehicle, plate]


class DemoOCRProcessor:
    def read_text(self, plate_crop) -> PlateOCRResult:
        return PlateOCRResult(
            raw_text=DEMO_PLATE_RAW,
            normalized_text=normalize_plate_text(DEMO_PLATE_RAW),
            confidence=0.94,
        )


class DemoPlateDetector:
    def detect_plates(self, frame: FramePacket, vehicle_boxes: List[BoundingBox]) -> List[NormalizedDetection]:
        dets = DemoDetectionEngine().detect(frame)
        return [d for d in dets if d.object_class == "LICENSE_PLATE"]


class DemoANPREngine:
    def recognize(self, frame: FramePacket) -> List[NormalizedDetection]:
        return DemoDetectionEngine().detect(frame)


class DemoInferenceEngine:
    """Replaceable demo engine used when DEMO_AI_MODE=true or no weights are configured."""

    def infer(self, frame: FramePacket) -> InferenceBatchResult:
        started = time.perf_counter()
        cfg = load_ai_config()
        detections = DemoDetectionEngine().detect(frame)
        elapsed = (time.perf_counter() - started) * 1000.0
        for det in detections:
            det.inference_time_ms = round(elapsed, 3)
            det.device = cfg.device
        return InferenceBatchResult(
            camera_id=frame.camera_id,
            timestamp=frame.timestamp,
            model_name="phantom-demo-detector",
            model_version="demo-1.0.0",
            device=cfg.device,
            inference_time_ms=round(elapsed, 3),
            detections=detections,
            frame_reference=frame.frame_reference,
            source_camera_id=frame.source_camera_id,
            source_system_id=frame.source_system_id,
            is_demo=True,
            metadata={"origin": "DEMO_AI_MODE", "not_live_cctv": True},
        )


class UltralyticsDetectionEngine:
    """Optional YOLO-compatible detector. Loaded only if ultralytics is installed and a path is set."""

    def __init__(self, model_path: str, device: str):
        from ultralytics import YOLO  # type: ignore

        self.device = device
        self.model = YOLO(model_path)

    def detect(self, frame: FramePacket) -> List[NormalizedDetection]:
        cfg = load_ai_config()
        if frame.image is None:
            return []
        results = self.model.predict(
            source=frame.image,
            conf=cfg.confidence_threshold,
            iou=cfg.iou_threshold,
            device=self.device,
            verbose=False,
        )
        detections: List[NormalizedDetection] = []
        for result in results:
            names = result.names or {}
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                xyxy = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                raw = names.get(cls_id, str(cls_id))
                try:
                    phantom_cls = normalize_detection_class(raw)
                except ValueError:
                    continue
                try:
                    bbox = parse_bbox(xyxy)
                    conf = validate_confidence(conf)
                except Exception:
                    continue
                detections.append(
                    NormalizedDetection(
                        detection_id=str(uuid.uuid4()),
                        camera_id=frame.camera_id,
                        timestamp=frame.timestamp,
                        object_class=phantom_cls,
                        confidence=conf,
                        bounding_box=bbox,
                        model_name=cfg.model_name,
                        model_version=cfg.model_version,
                        frame_reference=frame.frame_reference,
                        source_camera_id=frame.source_camera_id,
                        source_system_id=frame.source_system_id,
                        is_demo=False,
                        raw_model_class=str(raw),
                    )
                )
        return detections


def build_inference_engine() -> InferenceEngine:
    cfg = load_ai_config()
    if cfg.demo_mode or not cfg.model_path:
        return DemoInferenceEngine()
    try:
        detector = UltralyticsDetectionEngine(cfg.model_path, cfg.device)

        class Wrapped(DemoInferenceEngine):
            def infer(self, frame: FramePacket) -> InferenceBatchResult:
                started = time.perf_counter()
                dets = detector.detect(frame)
                elapsed = (time.perf_counter() - started) * 1000.0
                return InferenceBatchResult(
                    camera_id=frame.camera_id,
                    timestamp=frame.timestamp,
                    model_name=cfg.model_name,
                    model_version=cfg.model_version,
                    device=cfg.device,
                    inference_time_ms=round(elapsed, 3),
                    detections=dets,
                    frame_reference=frame.frame_reference,
                    source_camera_id=frame.source_camera_id,
                    source_system_id=frame.source_system_id,
                    is_demo=False,
                )

        return Wrapped()
    except Exception:
        return DemoInferenceEngine()
