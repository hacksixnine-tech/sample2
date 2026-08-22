import uuid
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_incidents_crud_and_linking(client: AsyncClient):
    investigator_token = create_access_token(
        subject=str(uuid.uuid4()),
        extra_claims={"role": "INVESTIGATOR", "department": "GUJ-POLICE"},
    )
    headers = {"Authorization": f"Bearer {investigator_token}"}

    # 1. Create Incident
    code = f"INC-TEST-{uuid.uuid4().hex[:6].upper()}"
    incident_payload = {
        "incident_code": code,
        "title": f"Organized Vehicle Theft Ring - Case {code}",
        "description": "Cross-district investigation tracking organized syndicate vehicles.",
        "severity": "CRITICAL",
        "status": "OPEN",
    }
    create_resp = await client.post("/api/v1/incidents", json=incident_payload, headers=headers)
    assert create_resp.status_code == 201, create_resp.text
    inc_data = create_resp.json()["data"]
    inc_id = inc_data["id"]
    assert inc_data["incident_code"] == code
    assert inc_data["status"] == "OPEN"

    # 2. Get Incident
    get_resp = await client.get(f"/api/v1/incidents/{inc_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["id"] == inc_id

    # 3. List Incidents
    list_resp = await client.get("/api/v1/incidents?status=OPEN", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) >= 1

    # 4. Update Incident status to INVESTIGATING
    patch_resp = await client.patch(
        f"/api/v1/incidents/{inc_id}",
        json={"status": "INVESTIGATING", "title": "Updated Title"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["status"] == "INVESTIGATING"
