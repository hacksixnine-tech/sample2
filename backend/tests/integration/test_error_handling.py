import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_404_standard_error_response(client: AsyncClient):
    response = await client.get("/api/v1/non_existent_endpoint")
    assert response.status_code == 404
    data = response.json()

    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "HTTP_404"
    assert "Not Found" in data["error"]["message"]
    assert "request_id" in data
    assert data["request_id"] is not None


@pytest.mark.asyncio
async def test_error_response_contains_request_id(client: AsyncClient):
    custom_trace = "trace-err-998877"
    response = await client.get("/invalid_path", headers={"X-Request-ID": custom_trace})
    assert response.status_code == 404
    data = response.json()
    assert data["request_id"] == custom_trace
