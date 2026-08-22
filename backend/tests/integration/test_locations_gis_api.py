import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_locations_list_and_filter(client: AsyncClient):
    response = await client.get("/api/v1/locations?district=Ahmedabad")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) > 0
    for loc in body["data"]:
        assert loc["district"] == "Ahmedabad"


@pytest.mark.asyncio
async def test_location_nearby_postgis_search(client: AsyncClient):
    # Income Tax Circle coordinates (23.0402, 72.5658) in Ahmedabad
    response = await client.get(
        "/api/v1/locations/nearby?latitude=23.0402&longitude=72.5658&radius_meters=5000"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    nearby_locations = body["data"]
    assert len(nearby_locations) > 0

    # Ensure results are sorted ascending by distance_meters
    distances = [loc["distance_meters"] for loc in nearby_locations]
    assert distances == sorted(distances)
    assert distances[0] <= 5000.0


@pytest.mark.asyncio
async def test_location_invalid_coordinates_rejection(client: AsyncClient):
    # Latitude 105.0 is out of bounds
    response = await client.get(
        "/api/v1/locations/nearby?latitude=105.0&longitude=72.5658"
    )
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_create_and_delete_location(client: AsyncClient):
    loc_payload = {
        "name": "Sabarmati Ashram North Gate",
        "state": "Gujarat",
        "district": "Ahmedabad",
        "city": "Ahmedabad",
        "address": "Gandhi Smarak Rd, Old Wadaj",
        "latitude": 23.0605,
        "longitude": 72.5801,
    }
    create_res = await client.post("/api/v1/locations", json=loc_payload)
    assert create_res.status_code == 201
    created_loc = create_res.json()["data"]
    loc_id = created_loc["id"]

    # Delete Location
    del_res = await client.delete(f"/api/v1/locations/{loc_id}")
    assert del_res.status_code == 200
