import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_departments_seeded_data(client: AsyncClient):
    response = await client.get("/api/v1/departments?page_size=30")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "data" in body
    assert body["pagination"]["total"] >= 26  # Seeded 26 Gujarat Government departments
    codes = [d["code"] for d in body["data"]]
    assert "GUJ-POLICE" in codes
    assert "RTO-GUJ" in codes


@pytest.mark.asyncio
async def test_department_crud_and_duplicate_rejection(client: AsyncClient):
    # 1. Create new department
    import uuid
    rand_code = f"GUJ-COAST-{uuid.uuid4().hex[:4].upper()}"
    new_dept = {
        "name": "Gujarat Coastal Security Command",
        "code": rand_code,
        "description": "Coastal and marine surveillance",
        "contact_email": "coastal@gujarat.gov.in",
        "contact_phone": "+91-79-23250000",
        "is_active": True,
    }
    create_res = await client.post("/api/v1/departments", json=new_dept)
    assert create_res.status_code == 201
    created_data = create_res.json()["data"]
    dept_id = created_data["id"]
    assert created_data["code"] == rand_code

    # 2. Duplicate rejection (409 Conflict)
    dup_res = await client.post("/api/v1/departments", json=new_dept)
    assert dup_res.status_code == 409
    dup_body = dup_res.json()
    assert dup_body["success"] is False
    assert dup_body["error"]["code"] == "CONFLICT"

    # 3. Get Department Details
    get_res = await client.get(f"/api/v1/departments/{dept_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["name"] == "Gujarat Coastal Security Command"

    # 4. Update Department
    update_res = await client.patch(
        f"/api/v1/departments/{dept_id}",
        json={"name": "Gujarat Coastal & Island Command"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["name"] == "Gujarat Coastal & Island Command"

    # 5. Soft Delete / Deactivate
    del_res = await client.delete(f"/api/v1/departments/{dept_id}")
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_department_camera_summary(client: AsyncClient):
    # Retrieve Police department ID
    list_res = await client.get("/api/v1/departments?search=Police")
    assert list_res.status_code == 200
    depts = list_res.json()["data"]
    assert len(depts) > 0
    police_dept = depts[0]

    # Get department camera summary
    summary_res = await client.get(f"/api/v1/departments/{police_dept['id']}/cameras")
    assert summary_res.status_code == 200
    summary_data = summary_res.json()["data"]
    assert summary_data["department_code"] == police_dept["code"]
    assert "total_cameras" in summary_data
    assert "online_cameras" in summary_data
    assert "camera_types" in summary_data
    assert "district_distribution" in summary_data
