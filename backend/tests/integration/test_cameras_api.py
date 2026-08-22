import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_cameras_seeded_data(client: AsyncClient):
    response = await client.get("/api/v1/cameras?page_size=50")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["pagination"]["total"] >= 30  # At least 30 seeded cameras


@pytest.mark.asyncio
async def test_cameras_nearby_gis_search(client: AsyncClient):
    # Search around Income Tax Circle (23.0402, 72.5658) in Ahmedabad
    response = await client.get(
        "/api/v1/cameras/nearby?latitude=23.0402&longitude=72.5658&radius_meters=6000"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) > 0

    first_camera = body["data"][0]
    assert "camera_code" in first_camera
    assert "distance_meters" in first_camera
    assert first_camera["distance_meters"] <= 6000.0


@pytest.mark.asyncio
async def test_camera_coverage_statistics(client: AsyncClient):
    response = await client.get("/api/v1/cameras/coverage")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_cameras"] >= 30
    assert len(data["cameras_by_department"]) > 0
    assert len(data["cameras_by_district"]) > 0
    assert "online_percentage" in data


@pytest.mark.asyncio
async def test_camera_detail_with_eager_relations(client: AsyncClient):
    # Fetch first camera
    list_res = await client.get("/api/v1/cameras?page_size=1")
    assert list_res.status_code == 200
    cameras = list_res.json()["data"]
    assert len(cameras) > 0
    cam_id = cameras[0]["id"]

    # Fetch detail
    detail_res = await client.get(f"/api/v1/cameras/{cam_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()["data"]
    assert "department" in detail
    assert "location" in detail
    assert "streams" in detail
    assert "camera_code" in detail


@pytest.mark.asyncio
async def test_camera_create_duplicate_rejection_and_decommission(client: AsyncClient):
    # Get a department and location ID
    dept_res = await client.get("/api/v1/departments?page_size=1")
    dept_id = dept_res.json()["data"][0]["id"]

    loc_res = await client.get("/api/v1/locations?page_size=1")
    loc_id = loc_res.json()["data"][0]["id"]

    import uuid
    rand_code = f"CAM-TEST-GANDHI-{uuid.uuid4().hex[:6].upper()}"
    new_cam = {
        "camera_code": rand_code,
        "name": "Gandhinagar Gate 1 ANPR",
        "department_id": dept_id,
        "location_id": loc_id,
        "camera_type": "ANPR",
        "manufacturer": "Hikvision",
        "model": "iDS-2CD7A46G0/P-IZHS",
        "ownership": "Gujarat Government",
        "status": "ACTIVE",
        "connectivity_status": "ONLINE",
        "storage_type": "EDGE_AND_CENTRAL",
        "retention_days": 30,
    }

    # 1. Create camera
    create_res = await client.post("/api/v1/cameras", json=new_cam)
    assert create_res.status_code == 201
    created_cam = create_res.json()["data"]
    cam_id = created_cam["id"]

    # 2. Duplicate rejection (409 Conflict)
    dup_res = await client.post("/api/v1/cameras", json=new_cam)
    assert dup_res.status_code == 409

    # 3. Decommission / soft delete
    del_res = await client.delete(f"/api/v1/cameras/{cam_id}")
    assert del_res.status_code == 200

    # Verify status changed to DECOMMISSIONED
    get_res = await client.get(f"/api/v1/cameras/{cam_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["status"] == "DECOMMISSIONED"
