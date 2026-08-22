import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_and_get_sources(client: AsyncClient):
    response = await client.get("/api/v1/sources")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) >= 1

    source = body["data"][0]
    assert source["name"] == "CCTV Control Room"
    assert "corp8" in source["base_url"]
    assert source["source_type"] == "EXTERNAL_PROVIDED_CCTV_SOURCE"


@pytest.mark.asyncio
async def test_probe_external_source_live(client: AsyncClient):
    # 1. Get Source ID
    sources_res = await client.get("/api/v1/sources")
    source_id = sources_res.json()["data"][0]["id"]

    # 2. Probe external source
    probe_res = await client.post(f"/api/v1/sources/{source_id}/probe")
    assert probe_res.status_code == 200
    probe_body = probe_res.json()
    assert probe_body["success"] is True
    result = probe_body["data"]["probe_result"]
    assert result["accessible"] is True
    assert result["total_cameras"] == 30


@pytest.mark.asyncio
async def test_discover_external_source_cameras(client: AsyncClient):
    # 1. Get Source ID
    sources_res = await client.get("/api/v1/sources")
    source_id = sources_res.json()["data"][0]["id"]

    # 2. Discover live cameras
    disc_res = await client.get(f"/api/v1/sources/{source_id}/discover")
    assert disc_res.status_code == 200
    disc_body = disc_res.json()
    assert disc_body["success"] is True
    disc_data = disc_body["data"]
    assert disc_data["total_discovered"] == 30
    assert len(disc_data["cameras"]) == 30

    first_cam = disc_data["cameras"][0]
    assert "source_camera_id" in first_cam
    assert len(first_cam["streams"]) >= 1
    protocols = [s["protocol"] for s in first_cam["streams"]]
    assert "RTSP" in protocols


@pytest.mark.asyncio
async def test_sync_source_cameras_into_phantom(client: AsyncClient):
    # 1. Get Source ID
    sources_res = await client.get("/api/v1/sources")
    source_id = sources_res.json()["data"][0]["id"]

    # 2. Sync cameras into PHANTOM registry
    sync_res = await client.post(f"/api/v1/sources/{source_id}/sync")
    assert sync_res.status_code == 200
    sync_body = sync_res.json()
    assert sync_body["success"] is True
    report = sync_body["data"]
    assert report["total_discovered"] == 30
    assert report["created_count"] + report["updated_count"] == 30
    assert report["error_count"] == 0

    # 3. Verify that cameras now exist in PHANTOM registry with source mapping
    cam_res = await client.get("/api/v1/cameras?search=SRC-CORP8-001")
    assert cam_res.status_code == 200
    cams = cam_res.json()["data"]
    assert len(cams) >= 1
    cam = cams[0]
    assert cam["source_system_id"] == source_id
    assert cam["source_camera_id"] == "1"
    assert cam["connectivity_status"] == "ONLINE"
