import logging
from typing import Any, List, Optional, Tuple
import uuid

import numpy as np

from app.ai.anpr.normalize import normalize_plate_text
from app.ai.anpr.ocr import build_ocr_processor
from app.ai.interfaces import BoundingBox, FramePacket, NormalizedDetection, PlateOCRResult

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

logger = logging.getLogger(__name__)

VEHICLE_CLASSES = {"CAR", "TRUCK", "BUS", "MOTORCYCLE", "OTHER_VEHICLE"}


class TwoStageANPREngine:
    """Two-stage Automatic Number Plate Recognition (ANPR) pipeline.
    
    Stage 1: Vehicle localization & plate region isolation.
    Stage 2: Image pre-processing (CLAHE, bilateral filter) + OCR + Plate Normalization.
    """

    def __init__(self, prefer_demo: bool = False):
        self.ocr_processor = build_ocr_processor(prefer_demo=prefer_demo)

    def extract_plate_from_vehicle_crop(
        self, vehicle_img: np.ndarray
    ) -> Tuple[Optional[np.ndarray], Optional[BoundingBox]]:
        """Isolates the most likely license plate sub-region from a vehicle bounding box crop."""
        if not CV2_AVAILABLE or vehicle_img is None or vehicle_img.size == 0:
            return None, None

        h, w = vehicle_img.shape[:2]
        if h < 20 or w < 20:
            return None, None

        # Standard Indian/International vehicle plate position: Lower 45% of vehicle, centered 80% width
        y1 = int(h * 0.55)
        y2 = int(h * 0.98)
        x1 = int(w * 0.10)
        x2 = int(w * 0.90)

        plate_crop = vehicle_img[y1:y2, x1:x2]
        rel_bbox = BoundingBox(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2))
        return plate_crop, rel_bbox

    def preprocess_plate_image(self, plate_img: np.ndarray) -> np.ndarray:
        """Applies contrast enhancement (CLAHE) and noise reduction for higher OCR accuracy."""
        if not CV2_AVAILABLE or plate_img is None or plate_img.size == 0:
            return plate_img

        try:
            # Convert to grayscale if 3-channel
            if len(plate_img.shape) == 3:
                gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = plate_img

            # Contrast Limited Adaptive Histogram Equalization (CLAHE)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Bilateral filter to smooth texture while preserving character edges
            filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)
            return filtered
        except Exception as e:
            logger.debug(f"Plate preprocessing fallback: {e}")
            return plate_img

    def process_detections(
        self, frame: FramePacket, detections: List[NormalizedDetection]
    ) -> List[NormalizedDetection]:
        """Runs ANPR OCR on all vehicle detections in the frame."""
        if frame.image is None:
            return detections

        img_arr = np.asarray(frame.image)
        h_frame, w_frame = img_arr.shape[:2]

        for det in detections:
            if det.object_class not in VEHICLE_CLASSES and det.object_class != "LICENSE_PLATE":
                continue

            # If already has normalized plate, skip
            if det.plate and det.plate.normalized_text:
                continue

            box = det.bounding_box
            bx1 = max(0, min(int(box.x1), w_frame - 1))
            by1 = max(0, min(int(box.y1), h_frame - 1))
            bx2 = max(0, min(int(box.x2), w_frame))
            by2 = max(0, min(int(box.y2), h_frame))

            if (bx2 - bx1) < 20 or (by2 - by1) < 20:
                continue

            vehicle_crop = img_arr[by1:by2, bx1:bx2]

            if det.object_class == "LICENSE_PLATE":
                plate_crop = vehicle_crop
                plate_rel_box = box
            else:
                plate_crop, plate_rel_box = self.extract_plate_from_vehicle_crop(vehicle_crop)

            if plate_crop is None or plate_crop.size == 0:
                continue

            preprocessed_crop = self.preprocess_plate_image(plate_crop)
            ocr_result = self.ocr_processor.read_text(preprocessed_crop)

            if ocr_result and ocr_result.normalized_text:
                det.plate = ocr_result
                if plate_rel_box and det.object_class != "LICENSE_PLATE":
                    # Map relative plate box back to full frame coordinates
                    det.plate_bbox = BoundingBox(
                        x1=float(bx1 + plate_rel_box.x1),
                        y1=float(by1 + plate_rel_box.y1),
                        x2=float(bx1 + plate_rel_box.x2),
                        y2=float(by1 + plate_rel_box.y2),
                    )
                elif det.object_class == "LICENSE_PLATE":
                    det.plate_bbox = box

        return detections


_global_anpr_engine: Optional[TwoStageANPREngine] = None


def get_global_anpr_engine(prefer_demo: bool = False) -> TwoStageANPREngine:
    global _global_anpr_engine
    if _global_anpr_engine is None:
        _global_anpr_engine = TwoStageANPREngine(prefer_demo=prefer_demo)
    return _global_anpr_engine
