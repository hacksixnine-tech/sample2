import threading
from collections import defaultdict
from typing import Any, Dict


class AIMetrics:
    """Process-local operational counters. Not a claim of model accuracy."""

    def __init__(self):
        self._lock = threading.Lock()
        self.frames_processed = 0
        self.detections = 0
        self.anpr_attempts = 0
        self.anpr_success = 0
        self.low_confidence_ocr = 0
        self.errors = 0
        self.inference_latency_ms_total = 0.0
        self.inference_latency_samples = 0
        self.queue_latency_ms_total = 0.0
        self.queue_latency_samples = 0
        self.processing_fps_samples = 0.0

    def incr(self, field: str, amount: int = 1) -> None:
        with self._lock:
            setattr(self, field, getattr(self, field) + amount)

    def observe_inference_ms(self, value: float) -> None:
        with self._lock:
            self.inference_latency_ms_total += value
            self.inference_latency_samples += 1

    def observe_queue_ms(self, value: float) -> None:
        with self._lock:
            self.queue_latency_ms_total += value
            self.queue_latency_samples += 1

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            inf_avg = (
                self.inference_latency_ms_total / self.inference_latency_samples
                if self.inference_latency_samples
                else None
            )
            q_avg = (
                self.queue_latency_ms_total / self.queue_latency_samples
                if self.queue_latency_samples
                else None
            )
            return {
                "frames_processed": self.frames_processed,
                "detections": self.detections,
                "anpr_attempts": self.anpr_attempts,
                "successful_anpr": self.anpr_success,
                "low_confidence_ocr": self.low_confidence_ocr,
                "inference_latency_ms_avg": inf_avg,
                "queue_latency_ms_avg": q_avg,
                "processing_fps": self.processing_fps_samples,
                "errors": self.errors,
                "note": "Operational counters only. Accuracy is not claimed without a measured benchmark.",
            }


metrics = AIMetrics()
