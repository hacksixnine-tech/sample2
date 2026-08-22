import time
from datetime import datetime, timezone
import uuid
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_synthetic_intelligence_performance(client: AsyncClient):
    """
    Synthetic load test to measure database and correlation pipeline latency.
    Runs 20 synthetic plate observations and measures end-to-end response time.
    """
    admin_token = create_access_token(
        subject=str(uuid.uuid4()), extra_claims={"role": "SYSTEM_ADMIN"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    worker_headers = {"X-PHANTOM-WORKER-KEY": "phantom_ai_worker_dev_key_2026"}

    cams_resp = await client.get("/api/v1/cameras")
    assert cams_resp.status_code == 200
    cam_id = cams_resp.json()["data"][0]["id"]

    # 1. Create a watchlist
    code = f"WL-PERF-{uuid.uuid4().hex[:6].upper()}"
    wl_resp = await client.post(
        "/api/v1/watchlists",
        json={
            "name": f"Performance Watchlist {code}",
            "code": code,
            "category": "STOLEN_VEHICLE",
            "priority": "HIGH",
        },
        headers=admin_headers,
    )
    assert wl_resp.status_code == 201
    wl_id = wl_resp.json()["data"]["id"]

    # 2. Add 5 target plates
    target_plates = [f"GJ01PF{i:04d}" for i in range(5)]
    for p in target_plates:
        await client.post(
            f"/api/v1/watchlists/{wl_id}/entries",
            json={
                "identifier": p,
                "entity_type": "VEHICLE",
                "reason": "Performance benchmark",
                "priority": "HIGH",
            },
            headers=admin_headers,
        )

    # 3. Ingest 20 synthetic observations (mix of hits and non-hits)
    now = datetime.now(timezone.utc)
    start_time = time.perf_counter()

    for i in range(20):
        plate = target_plates[i % len(target_plates)] if i % 2 == 0 else f"GJ01NONHIT{i:03d}"
        resp = await client.post(
            "/api/v1/anpr/observations",
            json={
                "camera_id": cam_id,
                "raw_plate": plate,
                "normalized_plate": plate,
                "plate_confidence": 0.95,
                "timestamp": now.isoformat(),
                "is_demo": True,
            },
            headers=worker_headers,
        )
        assert resp.status_code == 201

    elapsed = time.perf_counter() - start_time
    avg_per_obs_ms = (elapsed / 20.0) * 1000.0

    print(f"\n[PERFORMANCE BENCHMARK] 20 observations processed in {elapsed:.2f}s ({avg_per_obs_ms:.1f}ms/observation)")
    # Ensure average ingestion + correlation latency is reasonable for local development (< 1500ms/item under concurrent test execution)
    assert avg_per_obs_ms < 1500.0
