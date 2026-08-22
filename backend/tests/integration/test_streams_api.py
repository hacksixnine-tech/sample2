import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_streams_crud_lifecycle(client: AsyncClient):
    # 1. Get first camera
    list_res = await client.get("/api/v1/cameras?page_size=1")
    camera_id = list_res.json()["data"][0]["id"]

    # 2. Attach Stream
    stream_payload = {
        "protocol": "RTSP",
        "stream_url": f"rtsp://cctv.gujarat.gov.in/live/{camera_id}/sub",
        "resolution": "720p",
        "fps": 15.0,
        "codec": "H264",
        "is_primary": False,
        "is_active": True,
    }
    create_res = await client.post(
        f"/api/v1/cameras/{camera_id}/streams", json=stream_payload
    )
    assert create_res.status_code == 201
    created_stream = create_res.json()["data"]
    stream_id = created_stream["id"]

    # 3. List Streams
    list_streams_res = await client.get(f"/api/v1/cameras/{camera_id}/streams")
    assert list_streams_res.status_code == 200
    assert len(list_streams_res.json()["data"]) >= 1

    # 4. Get Stream Details
    get_res = await client.get(f"/api/v1/cameras/{camera_id}/streams/{stream_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["resolution"] == "720p"

    # 5. Update Stream (make primary)
    update_res = await client.patch(
        f"/api/v1/cameras/{camera_id}/streams/{stream_id}",
        json={"is_primary": True, "resolution": "1080p"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["is_primary"] is True

    # 6. Delete Stream
    del_res = await client.delete(f"/api/v1/cameras/{camera_id}/streams/{stream_id}")
    assert del_res.status_code == 200
