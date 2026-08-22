import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_v1_info(client: AsyncClient):
    response = await client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["application"] == "PHANTOM Video Intelligence Platform"
    assert data["api_prefix"] == "/api/v1"
    assert isinstance(data["active_modules"], list)
    assert len(data["active_modules"]) > 0
