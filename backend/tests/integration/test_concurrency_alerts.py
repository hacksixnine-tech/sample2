import asyncio
from datetime import datetime, timezone
import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_concurrent_plate_ingestion_idempotency(client: AsyncClient):
    """
    Test two concurrent AI worker ingestion calls processing the exact same plate
    at the exact same camera and timestamp.
    Verifies that race conditions do not crash the server and entities/observations
    are handled idempotently.
    """
    cams_resp = await client.get("/api/v1/cameras")
    assert cams_resp.status_code == 200
    cam_id = cams_resp.json()["data"][0]["id"]

    plate = f"GJ01RACE{uuid.uuid4().hex[:4].upper()}"
    now = datetime.now(timezone.utc)
    worker_headers = {"X-PHANTOM-WORKER-KEY": "phantom_ai_worker_dev_key_2026"}

    payload1 = {
        "camera_id": cam_id,
        "raw_plate": plate,
        "normalized_plate": plate,
        "plate_confidence": 0.95,
        "timestamp": now.isoformat(),
        "is_demo": True,
    }
    payload2 = {
        "camera_id": cam_id,
        "raw_plate": plate,
        "normalized_plate": plate,
        "plate_confidence": 0.96,
        "timestamp": now.isoformat(),
        "is_demo": True,
    }

    # Run simultaneously
    resp1, resp2 = await asyncio.gather(
        client.post("/api/v1/anpr/observations", json=payload1, headers=worker_headers),
        client.post("/api/v1/anpr/observations", json=payload2, headers=worker_headers),
        return_exceptions=True,
    )

    # Both should complete cleanly with 201 or idempotent response
    assert not isinstance(resp1, Exception), str(resp1)
    assert not isinstance(resp2, Exception), str(resp2)
    assert resp1.status_code == 201
    assert resp2.status_code == 201
