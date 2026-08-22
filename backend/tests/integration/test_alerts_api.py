import uuid
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_alerts_crud_and_lifecycle(client: AsyncClient):
    police_token = create_access_token(
        subject=str(uuid.uuid4()),
        extra_claims={"role": "POLICE_OFFICER", "department": "GUJ-POLICE"},
    )
    headers = {"Authorization": f"Bearer {police_token}"}

    # Fetch a seeded camera
    cams_resp = await client.get("/api/v1/cameras")
    assert cams_resp.status_code == 200
    cam_id = cams_resp.json()["data"][0]["id"]

    # 1. Create Alert
    code = f"ALT-TEST-{uuid.uuid4().hex[:6].upper()}"
    alert_payload = {
        "alert_code": code,
        "alert_type": "WATCHLIST_HIT",
        "severity": "CRITICAL",
        "title": "Suspect Vehicle GJ01TEST999 Observed",
        "message": "Vehicle triggered hotlist match at SG Highway.",
        "status": "NEW",
        "camera_id": cam_id,
        "reason": {
            "type": "WATCHLIST_MATCH",
            "match_type": "EXACT_PLATE",
            "plate": "GJ01TEST999",
            "confidence": 0.95,
            "watchlist": "Stolen Vehicles Hotlist",
            "camera": "SG Highway Cam 01",
        },
    }
    create_resp = await client.post("/api/v1/alerts", json=alert_payload, headers=headers)
    assert create_resp.status_code == 201, create_resp.text
    alert_data = create_resp.json()["data"]
    alert_id = alert_data["id"]
    assert alert_data["status"] == "NEW"
    assert alert_data["severity"] == "CRITICAL"
    assert alert_data["reason"]["plate"] == "GJ01TEST999"

    # 2. Get Alert
    get_resp = await client.get(f"/api/v1/alerts/{alert_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["id"] == alert_id

    # 3. List Alerts
    list_resp = await client.get("/api/v1/alerts?status=NEW", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) >= 1

    # 4. Acknowledge Alert (NEW -> ACKNOWLEDGED)
    ack_resp = await client.post(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        json={"notes": "Control room dispatched PCR van"},
        headers=headers,
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["data"]["status"] == "ACKNOWLEDGED"

    # 5. Resolve Alert (ACKNOWLEDGED -> RESOLVED)
    res_resp = await client.post(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"resolution_notes": "Vehicle apprehended and secured by team"},
        headers=headers,
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["data"]["status"] == "RESOLVED"

    # 6. Invalid transition test: RESOLVED cannot be dismissed
    inv_resp = await client.post(
        f"/api/v1/alerts/{alert_id}/dismiss",
        json={"dismissal_reason": "Trying to dismiss a resolved alert"},
        headers=headers,
    )
    assert inv_resp.status_code == 422 or inv_resp.status_code == 400
