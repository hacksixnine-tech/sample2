import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_bulk_camera_import_structured_and_csv(client: AsyncClient):
    import uuid
    code1 = f"CAM-IMP-1-{uuid.uuid4().hex[:4].upper()}"
    code2 = f"CAM-IMP-2-{uuid.uuid4().hex[:4].upper()}"
    csv_content = (
        "camera_code,name,department_code,location_name,district,city,latitude,longitude,camera_type,stream_url\n"
        f"{code1},Expressway Toll 1,RTO-GUJ,NE1 Expressway Toll,Ahmedabad,Ahmedabad,23.01,72.60,ANPR,rtsp://stream1\n"
        f"{code2},Expressway Toll 2,RTO-GUJ,NE1 Expressway Toll,Ahmedabad,Ahmedabad,23.02,72.61,ANPR,rtsp://stream2\n"
        "CAM-IMPORT-DUP,Duplicate Test,INVALID_DEPT,Invalid Junction,Ahmedabad,Ahmedabad,23.03,72.62,ANPR,rtsp://stream3\n"
        "CAM-IMPORT-003,Out of bounds test,RTO-GUJ,Bad Loc,Ahmedabad,Ahmedabad,123.45,72.63,ANPR,rtsp://stream4\n"
    )

    files = {"file": ("cameras.csv", csv_content, "text/csv")}
    response = await client.post("/api/v1/cameras/bulk-import", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    report = body["data"]

    # 4 total rows: 2 valid, 1 invalid dept, 1 invalid coordinates
    assert report["total_rows"] == 4
    assert report["successful"] == 2
    assert report["failed"] == 2
    assert code1 in report["imported_camera_codes"]
    assert code2 in report["imported_camera_codes"]
    assert len(report["errors"]) == 2

    # Verify that valid cameras actually exist in database
    get_res = await client.get(f"/api/v1/cameras?search={code1}")
    assert get_res.status_code == 200
    assert len(get_res.json()["data"]) == 1
