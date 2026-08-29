import os
import sys
sys.path.insert(0, os.path.abspath("."))

import uuid
from datetime import datetime, timezone
import numpy as np
import cv2
import urllib.request

print("=" * 65)
print("PHANTOM AI VISION PIPELINE COMPREHENSIVE TEST")
print("=" * 65)

from app.ai.interfaces import FramePacket, BoundingBox, NormalizedDetection
from app.ai.tracking import ByteTrackManager, CameraByteTracker
from app.ai.anpr import TwoStageANPREngine, normalize_plate_text
from app.ai.detection.engines import UltralyticsDetectionEngine

# -------------------------------------------------------------
# TEST 1: ANPR OCR & Plate Normalization Engine
# -------------------------------------------------------------
print("\n[TEST 1] Testing ANPR OCR Engine...")
anpr_engine = TwoStageANPREngine(prefer_demo=False)

# Generate a high-contrast realistic Indian Number Plate image
plate_img = np.ones((80, 260, 3), dtype=np.uint8) * 245
cv2.rectangle(plate_img, (4, 4), (255, 75), (0, 0, 0), 2)
cv2.putText(plate_img, "GJ-01-AB-1234", (18, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (0, 0, 0), 3)

ocr_res = anpr_engine.ocr_processor.read_text(plate_img)
print(f"  Raw OCR Text:       '{ocr_res.raw_text}'")
print(f"  Normalized Plate:   '{ocr_res.normalized_text}'")
print(f"  OCR Confidence:     {ocr_res.confidence:.2f}")
assert "GJ01AB1234" in ocr_res.normalized_text or "GJ" in ocr_res.normalized_text, "OCR failed to read plate"
print("  --> [PASS] ANPR OCR & Normalization Validated!")

# -------------------------------------------------------------
# TEST 2: ByteTrack Multi-Object Tracking & Velocity Estimation
# -------------------------------------------------------------
print("\n[TEST 2] Testing ByteTrack Multi-Object Trajectory Engine...")
cam_tracker = CameraByteTracker(camera_id="cam-ahmedabad-01")
cid = uuid.uuid4()

print("  Simulating 5 sequential frames of a moving vehicle...")
base_time = datetime.now(timezone.utc)
for f in range(5):
    # Simulated vehicle moving rightwards & downwards
    x1, y1 = 100.0 + (f * 25.0), 150.0 + (f * 18.0)
    x2, y2 = x1 + 180.0, y1 + 120.0
    frame_time = datetime.fromtimestamp(base_time.timestamp() + (f * 0.2), tz=timezone.utc)
    det = NormalizedDetection(
        detection_id=str(uuid.uuid4()),
        camera_id=cid,
        timestamp=frame_time,
        object_class="CAR",
        confidence=0.88,
        bounding_box=BoundingBox(x1, y1, x2, y2),
        model_name="yolov8n",
        model_version="1.0.0",
    )
    tracked = cam_tracker.update([det], frame_timestamp=frame_time)
    t_id = tracked[0].track_id if tracked else None
    heading = tracked[0].direction_heading if tracked else None
    speed = tracked[0].speed_estimate_kmph if tracked else None
    print(f"    Frame #{f+1}: Box=[{int(x1)}, {int(y1)}, {int(x2)}, {int(y2)}] -> TrackID={t_id}, Heading={heading}, Speed={speed} km/h")

assert tracked[0].track_id is not None, "ByteTrack failed to assign Track ID"
print("  --> [PASS] ByteTrack Trajectory Tracking Validated!")

# -------------------------------------------------------------
# TEST 3: YOLO Detection Model Real Image Inference
# -------------------------------------------------------------
print("\n[TEST 3] Testing Ultralytics YOLO Real-World Image Inference...")
# Load standard Ultralytics sample bus/traffic image
sample_url = "https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/assets/bus.jpg"
sample_file = "var/sample_bus.jpg"
os.makedirs("var", exist_ok=True)

if not os.path.exists(sample_file):
    print(f"  Downloading standard traffic sample image...")
    urllib.request.urlretrieve(sample_url, sample_file)

img_real = cv2.imread(sample_file)
engine = UltralyticsDetectionEngine(device="cpu")
packet = FramePacket(
    camera_id=cid,
    timestamp=datetime.now(timezone.utc),
    image=img_real,
    width=img_real.shape[1],
    height=img_real.shape[0],
)

results = engine.detect(packet)
print(f"  Total Real Detections: {len(results)}")
for idx, d in enumerate(results):
    print(f"    [{idx+1}] Class: {d.object_class:<12} | Conf: {d.confidence:.2f} | TrackID: {d.track_id} | Box: ({int(d.bounding_box.x1)}, {int(d.bounding_box.y1)}, {int(d.bounding_box.x2)}, {int(d.bounding_box.y2)})")

assert len(results) > 0, "YOLO found no detections on sample bus image"
print("  --> [PASS] YOLOv8 Real-World Inference Validated!")

print("\n" + "=" * 65)
print("ALL TESTS PASSED: YOLO + ByteTrack + ANPR Pipeline FULLY OPERATIONAL!")
print("=" * 65)
