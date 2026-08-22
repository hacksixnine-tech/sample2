from datetime import datetime, timezone
from typing import Optional

from app.ai.configuration import load_ai_config
from app.ai.detection.engines import build_inference_engine
from app.ai.interfaces import FramePacket, InferenceBatchResult, InferenceEngine
from app.ai.metrics import metrics
from app.ai.preprocessing.frames import FrameProcessingWorker, preprocess_frame
from app.core.logging import logger


class InferenceWorker:
    """Compute-plane worker: sampled frames → replaceable InferenceEngine → normalized results."""

    def __init__(
        self,
        engine: Optional[InferenceEngine] = None,
        frame_worker: Optional[FrameProcessingWorker] = None,
    ):
        self.engine = engine or build_inference_engine()
        self.frame_worker = frame_worker or FrameProcessingWorker()
        self.cfg = load_ai_config()

    def process_frame(self, frame: FramePacket) -> Optional[InferenceBatchResult]:
        try:
            accepted = self.frame_worker.accept(frame)
            if accepted is None:
                return None
            prepared = preprocess_frame(accepted)
            result = self.engine.infer(prepared)
            metrics.incr("frames_processed")
            metrics.incr("detections", len(result.detections))
            metrics.observe_inference_ms(result.inference_time_ms)
            for det in result.detections:
                if det.object_class == "LICENSE_PLATE":
                    metrics.incr("anpr_attempts")
                    if det.plate and det.plate.confidence >= self.cfg.ocr_threshold and det.plate.normalized_text:
                        metrics.incr("anpr_success")
                    else:
                        metrics.incr("low_confidence_ocr")
            return result
        except Exception as exc:
            metrics.incr("errors")
            logger.exception(f"Inference worker failed without crashing API: {exc}")
            return None
