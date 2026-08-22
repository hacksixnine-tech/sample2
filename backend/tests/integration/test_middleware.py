import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_request_id_generated_automatically(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 10


@pytest.mark.asyncio
async def test_custom_request_id_propagated(client: AsyncClient):
    custom_id = "test-custom-trace-id-12345"
    response = await client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id
