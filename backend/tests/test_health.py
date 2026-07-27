from uuid import UUID

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
    UUID(response.headers["X-Request-ID"])


@pytest.mark.asyncio
async def test_valid_correlation_id_is_returned_as_request_id() -> None:
    request_id = "85db1ec3-63f4-492c-a293-8b6d2f6e71c9"
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/health",
            headers={"X-Correlation-ID": request_id},
        )

    assert response.headers["X-Request-ID"] == request_id


@pytest.mark.asyncio
async def test_invalid_correlation_id_is_replaced() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/health",
            headers={"X-Correlation-ID": "not-a-safe-id"},
        )

    generated_id = response.headers["X-Request-ID"]
    UUID(generated_id)
    assert generated_id != "not-a-safe-id"


@pytest.mark.asyncio
async def test_metrics_use_route_templates_instead_of_raw_paths() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/api/v1/health")
        await client.get("/not-found-with-user-controlled-value")
        response = await client.get("/api/v1/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert 'route="/health",status="200"} 1' in response.text
    assert 'route="unmatched",status="404"} 1' in response.text
    assert "not-found-with-user-controlled-value" not in response.text
    assert "bet_score_live_connections 0" in response.text
    assert "bet_score_live_connection_rejections_total 0" in response.text
