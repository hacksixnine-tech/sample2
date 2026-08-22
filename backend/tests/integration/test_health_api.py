import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_camera_health_summary(client: AsyncClient):
    response = await client.get("/api/v1/cameras/health/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    summary = body["data"]
    assert summary["total"] >= 30
    assert summary["online"] >= 1
    assert "offline" in summary
    assert "degraded" in summary


@pytest.mark.asyncio
async def test_record_and_get_camera_health(client: AsyncClient):
    # 1. Get first camera
    list_res = await client.get("/api/v1/cameras?page_size=1")
    camera_id = list_res.json()["data"][0]["id"]

    # 2. Record health heartbeat
    health_payload = {
        "status": "ONLINE",
        "latency_ms": 18,
        "packet_loss_pct": 0.05,
        "current_fps": 24.8,
        "bitrate_kbps": 4096,
        "health_score": 98.5,
    }
    record_res = await client.post(
        f"/api/v1/cameras/{camera_id}/health", json=health_payload
    )
    assert record_res.status_code == 201
    recorded_data = record_res.json()["data"]
    assert recorded_data["status"] == "ONLINE"
    assert recorded_data["latency_ms"] == 18

    # 3. Get latest health
    get_res = await client.get(f"/api/v1/cameras/{camera_id}/health")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["status"] == "ONLINE"

    # 4. Get health history
    history_res = await client.get(f"/api/v1/cameras/{camera_id}/health/history")
    assert history_res.status_code == 200
    assert len(history_res.json()["data"]) >= 1
