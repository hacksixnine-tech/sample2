from datetime import datetime, timezone
import uuid
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_investigations_search_and_dossier_flow(client: AsyncClient):
    analyst_token = create_access_token(
        subject=str(uuid.uuid4()),
        extra_claims={"role": "ANALYST", "department": "GUJ-POLICE"},
    )
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # Fetch existing cameras
    cams_resp = await client.get("/api/v1/cameras")
    assert cams_resp.status_code == 200
    cameras = cams_resp.json()["data"]
    assert len(cameras) >= 2
    cam_a = cameras[0]["id"]
    cam_b = cameras[1]["id"]

    # Ingest 2 observations for a target vehicle
    plate = f"GJ01INVST{uuid.uuid4().hex[:4].upper()}"
    now = datetime.now(timezone.utc)

    worker_headers = {"X-PHANTOM-WORKER-KEY": "phantom_ai_worker_dev_key_2026"}

    # Observation 1 at Camera A
    obs1_payload = {
        "camera_id": cam_a,
        "raw_plate": plate,
        "normalized_plate": plate,
        "plate_confidence": 0.96,
        "timestamp": now.isoformat(),
        "is_demo": True,
    }
    resp1 = await client.post("/api/v1/anpr/observations", json=obs1_payload, headers=worker_headers)
    assert resp1.status_code == 201, resp1.text
    veh_id = resp1.json()["data"]["vehicle_id"]
    assert veh_id is not None

    # Observation 2 at Camera B (10 mins later)
    obs2_payload = {
        "camera_id": cam_b,
        "raw_plate": plate,
        "normalized_plate": plate,
        "plate_confidence": 0.94,
        "timestamp": (now).isoformat(),
        "is_demo": True,
    }
    resp2 = await client.post("/api/v1/anpr/observations", json=obs2_payload, headers=worker_headers)
    assert resp2.status_code == 201, resp2.text

    # 1. Multi-source Search
    search_resp = await client.get(f"/api/v1/investigations/search?plate={plate}", headers=headers)
    assert search_resp.status_code == 200
    search_data = search_resp.json()["data"]
    assert search_data["total_vehicles"] >= 1
    assert search_data["total_observations"] >= 1

    # 2. Vehicle Movement History
    hist_resp = await client.get(f"/api/v1/vehicles/{veh_id}/history", headers=headers)
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()["data"]
    assert hist_data["vehicle_id"] == veh_id
    assert hist_data["normalized_plate"] == plate
    assert hist_data["sighting_count"] >= 2

    # 3. GIS-Ready Route
    route_resp = await client.get(f"/api/v1/vehicles/{veh_id}/route", headers=headers)
    assert route_resp.status_code == 200
    route_data = route_resp.json()["data"]
    assert route_data["route_type"] == "OBSERVED_CAMERA_SEQUENCE"
    assert route_data["point_count"] >= 2
    assert "points" in route_data

    # 4. Vehicle Investigation Dossier
    dossier_resp = await client.get(f"/api/v1/investigations/vehicle/{veh_id}", headers=headers)
    assert dossier_resp.status_code == 200
    dossier_data = dossier_resp.json()["data"]
    assert dossier_data["plate"] == plate
    assert dossier_data["sighting_count"] >= 2

    # 5. Unified Forensic Timeline
    timeline_resp = await client.get(f"/api/v1/investigations/vehicle/{veh_id}/timeline", headers=headers)
    assert timeline_resp.status_code == 200
    tl_data = timeline_resp.json()["data"]
    assert tl_data["total_events"] >= 2
    assert len(tl_data["events"]) >= 2
