"""Optional CLI entry for the AI compute plane.

FastAPI must not decode video or run YOLO inside request handlers.
Run this process separately:

    python -m app.ai.workers.cli --demo

Authorized local sample video (not live.corp8.cloud) may be passed with --video.
Live source consumption is a stream-gateway concern; this worker only accepts FramePackets.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.ai.detection.engines import DemoInferenceEngine
from app.ai.interfaces import FramePacket
from app.ai.messaging import in_process_bus
from app.ai.workers.inference_worker import InferenceWorker


async def run_demo_once() -> None:
    worker = InferenceWorker(engine=DemoInferenceEngine())
    packet = FramePacket(
        camera_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        frame_reference="demo://sample-frame",
        is_demo=True,
        stream_metadata={"origin": "DEMO_AI_MODE"},
    )
    result = worker.process_frame(packet)
    if result:
        await in_process_bus.publish("ai.results", {"detections": len(result.detections), "is_demo": True})
        print(f"demo_inferences={len(result.detections)} plate_demo=GJ01TEST001")


def main() -> None:
    parser = argparse.ArgumentParser(description="PHANTOM AI inference worker")
    parser.add_argument("--demo", action="store_true", help="Run one deterministic DEMO inference")
    parser.add_argument("--video", help="Authorized local sample video path (not live CCTV)")
    args = parser.parse_args()
    if args.video:
        print("Local sample video adapters should emit FramePackets; live corp8 ingest is not fabricated here.")
    asyncio.run(run_demo_once())


if __name__ == "__main__":
    main()
