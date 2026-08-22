from datetime import datetime, timezone
import uuid
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_full_e2e_intelligence_workflow(client: AsyncClient):
    """
    End-to-End Deterministic Scenario:
    DEMO ANPR
       ↓
    DEMO WATCHLIST
       ↓
    MATCH
       ↓
    ALERT
       ↓
    INCIDENT
       ↓
    MULTI-CAMERA OBSERVATIONS
       ↓
    VEHICLE HISTORY
       ↓
    GIS ROUTE
       ↓
    INVESTIGATION TIMELINE
    """
    # Tokens for roles
    admin_token = create_access_token(
        subject=str(uuid.uuid4()), extra_claims={"role": "SYSTEM_ADMIN", "department": "GUJ-POLICE"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    worker_headers = {"X-PHANTOM-WORKER-KEY": "phantom_ai_worker_dev_key_2026"}

    # Fetch 2 cameras
    cams_resp = await client.get("/api/v1/cameras")
    assert cams_resp.status_code == 200
    cameras = cams_resp.json()["data"]
    cam_1 = cameras[0]["id"]
    cam_2 = cameras[1]["id"]

    # 1. Create Demo Watchlist
    wl_code = f"DEMO-WL-{uuid.uuid4().hex[:6].upper()}"
    wl_resp = await client.post(
        "/api/v1/watchlists",
        json={
            "name": f"PHANTOM DEMO VEHICLE WATCHLIST {wl_code}",
            "code": wl_code,
            "category": "STOLEN_VEHICLE",
            "priority": "CRITICAL",
            "description": "DEMO_ONLY watchlist for statewide vehicle tracking validation",
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert wl_resp.status_code == 201
    wl_id = wl_resp.json()["data"]["id"]

    # 2. Add Demo Vehicle to Watchlist
    demo_plate = f"GJ01TEST{uuid.uuid4().hex[:4].upper()}"
    entry_resp = await client.post(
        f"/api/v1/watchlists/{wl_id}/entries",
        json={
            "identifier": demo_plate,
            "entity_type": "VEHICLE",
            "case_reference_number": "FIR-DEMO-2026",
            "fir_station": "Ahmedabad Crime Branch",
            "reason": "DEMO_ONLY Stolen Vehicle Benchmark",
            "priority": "CRITICAL",
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert entry_resp.status_code == 201

    # 3. Generate ANPR Observation at Camera 1
    now = datetime.now(timezone.utc)
    anpr_resp1 = await client.post(
        "/api/v1/anpr/observations",
        json={
            "camera_id": cam_1,
            "raw_plate": demo_plate,
            "normalized_plate": demo_plate,
            "plate_confidence": 0.98,
            "timestamp": now.isoformat(),
            "is_demo": True,
        },
        headers=worker_headers,
    )
    assert anpr_resp1.status_code == 201
    veh_id = anpr_resp1.json()["data"]["vehicle_id"]
    assert veh_id is not None

    # 4. Verify Alert Generation from Watchlist Match
    alerts_resp = await client.get(f"/api/v1/alerts?entity_id={veh_id}", headers=admin_headers)
    assert alerts_resp.status_code == 200
    alerts_data = alerts_resp.json()["data"]
    assert len(alerts_data) >= 1
    alert_1 = alerts_data[0]
    alert_id = alert_1["id"]
    assert alert_1["severity"] == "CRITICAL"
    assert alert_1["status"] == "NEW"
    assert "reason" in alert_1
    assert alert_1["reason"]["plate"] == demo_plate

    # 5. Alert Deduplication: Send identical detection to Camera 1 immediately
    anpr_resp_dup = await client.post(
        "/api/v1/anpr/observations",
        json={
            "camera_id": cam_1,
            "raw_plate": demo_plate,
            "normalized_plate": demo_plate,
            "plate_confidence": 0.97,
            "timestamp": now.isoformat(),
            "is_demo": True,
        },
        headers=worker_headers,
    )
    assert anpr_resp_dup.status_code == 201
    # Check alert count didn't double
    alerts_check = await client.get(f"/api/v1/alerts?entity_id={veh_id}", headers=admin_headers)
    assert len(alerts_check.json()["data"]) == len(alerts_data)

    # 6. Acknowledge Alert
    ack_resp = await client.post(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        json={"notes": "Investigator tracking target in real-time"},
        headers=admin_headers,
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["data"]["status"] == "ACKNOWLEDGED"

    # 7. Create Incident and Link Alert
    inc_code = f"INC-DEMO-{uuid.uuid4().hex[:6].upper()}"
    inc_resp = await client.post(
        "/api/v1/incidents",
        json={
            "incident_code": inc_code,
            "title": f"Dossier for Stolen Vehicle {demo_plate}",
            "description": "Cross-camera pursuit operation.",
            "severity": "CRITICAL",
            "alert_ids": [alert_id],
            "entity_ids": [veh_id],
        },
        headers=admin_headers,
    )
    assert inc_resp.status_code == 201
    inc_id = inc_resp.json()["data"]["id"]

    # 8. Sighting at Camera 2 (Movement corridor)
    anpr_resp2 = await client.post(
        "/api/v1/anpr/observations",
        json={
            "camera_id": cam_2,
            "raw_plate": demo_plate,
            "normalized_plate": demo_plate,
            "plate_confidence": 0.95,
            "timestamp": now.isoformat(),
            "is_demo": True,
        },
        headers=worker_headers,
    )
    assert anpr_resp2.status_code == 201

    # 9. Vehicle History
    hist_resp = await client.get(f"/api/v1/vehicles/{veh_id}/history", headers=admin_headers)
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()["data"]
    assert hist_data["sighting_count"] >= 2

    # 10. GIS-Ready Route
    route_resp = await client.get(f"/api/v1/vehicles/{veh_id}/route", headers=admin_headers)
    assert route_resp.status_code == 200
    route_data = route_resp.json()["data"]
    assert route_data["route_type"] == "OBSERVED_CAMERA_SEQUENCE"
    assert len(route_data["points"]) >= 2

    # 11. Unified Forensic Timeline
    tl_resp = await client.get(f"/api/v1/investigations/vehicle/{veh_id}/timeline", headers=admin_headers)
    assert tl_resp.status_code == 200
    tl_data = tl_resp.json()["data"]
    assert tl_data["total_events"] >= 3  # Observations + Alert + Incident

    # 12. Investigation Dossier Summary
    dossier_resp = await client.get(f"/api/v1/investigations/vehicle/{veh_id}", headers=admin_headers)
    assert dossier_resp.status_code == 200
    dossier_data = dossier_resp.json()["data"]
    assert dossier_data["plate"] == demo_plate
    assert len(dossier_data["alerts"]) >= 1
    assert len(dossier_data["incidents"]) >= 1
