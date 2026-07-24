import pytest
from httpx import ASGITransport, AsyncClient

from bet_score.main import create_app


@pytest.mark.asyncio
async def test_health_returns_versioned_status() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
