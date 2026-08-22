from dataclasses import dataclass
from typing import Optional
from app.core.config import settings


@dataclass(frozen=True)
class AIRuntimeConfig:
    model_name: str
    model_version: str
    model_path: str
    confidence_threshold: float
    iou_threshold: float
    ocr_threshold: float
    frame_interval_fps: float
    device: str
    demo_mode: bool
    dedupe_window_seconds: float


def resolve_device(requested: Optional[str] = None) -> str:
    """Resolve compute device without assuming CUDA is present."""
    choice = (requested or settings.AI_DEVICE or "cpu").strip().lower()
    if choice in ("cuda", "gpu"):
        try:
            import torch  # type: ignore

            if torch.cuda.is_available():
                return "cuda"
        except Exception:
            pass
        return "cpu"
    return "cpu"


def load_ai_config() -> AIRuntimeConfig:
    return AIRuntimeConfig(
        model_name=settings.AI_MODEL_NAME,
        model_version=settings.AI_MODEL_VERSION,
        model_path=settings.AI_MODEL_PATH or "",
        confidence_threshold=float(settings.AI_CONFIDENCE_THRESHOLD),
        iou_threshold=float(settings.AI_IOU_THRESHOLD),
        ocr_threshold=float(settings.AI_OCR_THRESHOLD),
        frame_interval_fps=float(settings.AI_FRAME_INTERVAL_FPS),
        device=resolve_device(settings.AI_DEVICE),
        demo_mode=bool(settings.DEMO_AI_MODE),
        dedupe_window_seconds=float(settings.AI_DEDUPE_WINDOW_SECONDS),
    )


# Supported sampling presets (frames per second). Production rate is camera- and compute-dependent.
ALLOWED_SAMPLE_FPS = (1.0, 2.0, 5.0, 10.0)
