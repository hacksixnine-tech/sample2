from typing import Optional

from app.ai.interfaces import PHANTOM_DETECTION_CLASSES

# Model-specific labels → PHANTOM canonical classes. Never persist the left-hand keys.
_CLASS_ALIASES = {
    "person": "PERSON",
    "pedestrian": "PERSON",
    "human": "PERSON",
    "car": "CAR",
    "sedan": "CAR",
    "hatchback": "CAR",
    "suv": "CAR",
    "van": "CAR",
    "vehicle": "CAR",
    "auto": "CAR",
    "automobile": "CAR",
    "truck": "TRUCK",
    "lorry": "TRUCK",
    "pickup": "TRUCK",
    "bus": "BUS",
    "minibus": "BUS",
    "motorcycle": "MOTORCYCLE",
    "motorbike": "MOTORCYCLE",
    "scooter": "MOTORCYCLE",
    "two-wheeler": "MOTORCYCLE",
    "bicycle": "BICYCLE",
    "cycle": "BICYCLE",
    "license_plate": "LICENSE_PLATE",
    "licence_plate": "LICENSE_PLATE",
    "license-plate": "LICENSE_PLATE",
    "number_plate": "LICENSE_PLATE",
    "number plate": "LICENSE_PLATE",
    "plate": "LICENSE_PLATE",
    "anpr": "LICENSE_PLATE",
    "other_vehicle": "OTHER_VEHICLE",
    "other-vehicle": "OTHER_VEHICLE",
}


def normalize_detection_class(raw_label: Optional[str]) -> str:
    if raw_label is None:
        raise ValueError("detection class is required")
    token = str(raw_label).strip()
    if not token:
        raise ValueError("detection class is required")
    upper = token.upper().replace("-", "_").replace(" ", "_")
    if upper in PHANTOM_DETECTION_CLASSES:
        return upper
    mapped = _CLASS_ALIASES.get(token.lower().replace("_", " ").replace("-", " "))
    if mapped is None:
        mapped = _CLASS_ALIASES.get(token.lower().replace(" ", "_").replace("-", "_"))
    if mapped is None:
        # Last resort: common COCO ids as strings
        coco = {
            "2": "CAR",
            "3": "MOTORCYCLE",
            "5": "BUS",
            "7": "TRUCK",
            "0": "PERSON",
            "1": "BICYCLE",
        }
        mapped = coco.get(token)
    if mapped is None:
        raise ValueError(f"unsupported detection class: {raw_label}")
    return mapped


def phantom_class_to_detection_type(object_class: str) -> str:
    """Map PHANTOM class onto detections.detection_type CHECK values."""
    return object_class


def phantom_class_to_vehicle_type(object_class: str) -> str:
    mapping = {
        "CAR": "CAR",
        "TRUCK": "TRUCK",
        "BUS": "BUS",
        "MOTORCYCLE": "TWO_WHEELER",
        "BICYCLE": "TWO_WHEELER",
        "OTHER_VEHICLE": "OTHER",
    }
    return mapping.get(object_class, "OTHER")


def event_type_for_class(object_class: str) -> str:
    if object_class == "PERSON":
        return "PERSON_DETECTED"
    if object_class == "LICENSE_PLATE":
        return "PLATE_DETECTED"
    if object_class in {"CAR", "TRUCK", "BUS", "MOTORCYCLE", "BICYCLE", "OTHER_VEHICLE"}:
        return "VEHICLE_DETECTED"
    return "OBJECT_DETECTED"
