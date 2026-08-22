import uuid
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_watchlist_crud_and_entries_lifecycle(client: AsyncClient):
    admin_token = create_access_token(
        subject=str(uuid.uuid4()),
        extra_claims={"role": "SYSTEM_ADMIN", "department": "GUJ-POLICE"},
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create Watchlist
    code = f"WL-TEST-{uuid.uuid4().hex[:6].upper()}"
    create_payload = {
        "name": f"Test Stolen Vehicles Hotlist {code}",
        "code": code,
        "category": "STOLEN_VEHICLE",
        "priority": "HIGH",
        "description": "Integration test watchlist for stolen vehicles",
        "is_active": True,
        "metadata": {"test": True},
    }
    resp = await client.post("/api/v1/watchlists", json=create_payload, headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["success"] is True
    wl_id = body["data"]["id"]
    assert body["data"]["category"] == "STOLEN_VEHICLES"
    assert body["data"]["code"] == code

    # 2. Get Watchlist
    get_resp = await client.get(f"/api/v1/watchlists/{wl_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["id"] == wl_id

    # 3. Add Entry to Watchlist
    entry_payload = {
        "identifier": "GJ01TEST001",
        "entity_type": "VEHICLE",
        "case_reference_number": "FIR-TEST-9999",
        "fir_station": "Satellite PS",
        "reason": "Test stolen vehicle tracking",
        "priority": "CRITICAL",
        "is_active": True,
    }
    entry_resp = await client.post(
        f"/api/v1/watchlists/{wl_id}/entries", json=entry_payload, headers=headers
    )
    assert entry_resp.status_code == 201, entry_resp.text
    entry_data = entry_resp.json()["data"]
    entry_id = entry_data["id"]
    assert entry_data["normalized_identifier"] == "GJ01TEST001"
    assert entry_data["priority"] == "CRITICAL"

    # 4. List Entries
    list_entries_resp = await client.get(
        f"/api/v1/watchlists/{wl_id}/entries", headers=headers
    )
    assert list_entries_resp.status_code == 200
    assert len(list_entries_resp.json()["data"]) >= 1

    # 5. Update Entry
    patch_resp = await client.patch(
        f"/api/v1/watchlists/{wl_id}/entries/{entry_id}",
        json={"priority": "HIGH", "reason": "Updated reason"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["priority"] == "HIGH"

    # 6. Deactivate Watchlist Entry
    del_entry_resp = await client.delete(
        f"/api/v1/watchlists/{wl_id}/entries/{entry_id}", headers=headers
    )
    assert del_entry_resp.status_code == 200

    # 7. Deactivate Watchlist
    del_wl_resp = await client.delete(f"/api/v1/watchlists/{wl_id}", headers=headers)
    assert del_wl_resp.status_code == 200


@pytest.mark.asyncio
async def test_watchlist_category_validation_rejection(client: AsyncClient):
    admin_token = create_access_token(
        subject=str(uuid.uuid4()),
        extra_claims={"role": "SYSTEM_ADMIN"},
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    payload = {
        "name": "Invalid Category Watchlist",
        "code": f"WL-INV-{uuid.uuid4().hex[:6]}",
        "category": "ARBITRARY_UNCONTROLLED_CATEGORY_XYZ",
        "priority": "HIGH",
    }
    resp = await client.post("/api/v1/watchlists", json=payload, headers=headers)
    assert resp.status_code == 422 or resp.status_code == 400


@pytest.mark.asyncio
async def test_watchlist_unauthorized_access(client: AsyncClient):
    viewer_token = create_access_token(
        subject=str(uuid.uuid4()),
        extra_claims={"role": "VIEWER"},
    )
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    payload = {
        "name": "Should Fail",
        "code": f"WL-FAIL-{uuid.uuid4().hex[:6]}",
        "category": "STOLEN_VEHICLE",
        "priority": "HIGH",
    }
    # Viewer cannot create watchlist (403 Forbidden)
    resp = await client.post("/api/v1/watchlists", json=payload, headers=viewer_headers)
    assert resp.status_code == 403
