from typing import Optional

from app.ai.interfaces import BoundingBox
from app.core.exceptions import ValidationError


def validate_confidence(value: float, field: str = "confidence") -> float:
    try:
        conf = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be a number between 0.0 and 1.0") from exc
    if conf < 0.0 or conf > 1.0:
        raise ValidationError(f"{field} must be between 0.0 and 1.0")
    return conf


def parse_bbox(raw) -> BoundingBox:
    if raw is None:
        raise ValidationError("bounding_box is required")

    if isinstance(raw, BoundingBox):
        box = raw
    elif isinstance(raw, (list, tuple)) and len(raw) == 4:
        box = BoundingBox(x1=float(raw[0]), y1=float(raw[1]), x2=float(raw[2]), y2=float(raw[3]))
    elif isinstance(raw, dict):
        if all(k in raw for k in ("x1", "y1", "x2", "y2")):
            box = BoundingBox(
                x1=float(raw["x1"]),
                y1=float(raw["y1"]),
                x2=float(raw["x2"]),
                y2=float(raw["y2"]),
            )
        elif all(k in raw for k in ("x_min", "y_min", "x_max", "y_max")):
            box = BoundingBox(
                x1=float(raw["x_min"]),
                y1=float(raw["y_min"]),
                x2=float(raw["x_max"]),
                y2=float(raw["y_max"]),
            )
        else:
            raise ValidationError("bounding_box must include x1,y1,x2,y2")
    else:
        raise ValidationError("bounding_box must be [x1,y1,x2,y2] or an object with x1/y1/x2/y2")

    if any(v != v or v in (float("inf"), float("-inf")) for v in (box.x1, box.y1, box.x2, box.y2)):
        raise ValidationError("bounding_box coordinates must be finite numbers")
    if box.x2 < box.x1 or box.y2 < box.y1:
        raise ValidationError("bounding_box must satisfy x2 >= x1 and y2 >= y1")
    return box


def meets_ocr_threshold(confidence: float, threshold: float) -> bool:
    return validate_confidence(confidence, "ocr_confidence") >= threshold
