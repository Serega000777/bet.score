import asyncio
import os

import pytest
from httpx import ASGITransport, AsyncClient
from pytest import MonkeyPatch

from bet_score.application.readiness import ReadinessService
from bet_score.config import get_settings
from bet_score.infrastructure.readiness import probe_redis
from bet_score.main import create_app
from bet_score.presentation.api.dependencies import get_readiness_service


async def successful_probe() -> None:
    return None


async def failed_probe() -> None:
    raise OSError("dependency is unavailable")


async def slow_probe() -> None:
    await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_readiness_returns_ok_for_available_dependencies() -> None:
    application = create_app()
    application.dependency_overrides[get_readiness_service] = lambda: ReadinessService(
        {"postgres": successful_probe, "redis": successful_probe},
        timeout_seconds=0.1,
    )
    transport = ASGITransport(app=application)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {
        "status": "ready",
        "checks": {"postgres": "ok", "redis": "ok"},
    }


@pytest.mark.asyncio
async def test_readiness_returns_sanitized_503_for_failed_dependency() -> None:
    application = create_app()
    application.dependency_overrides[get_readiness_service] = lambda: ReadinessService(
        {"postgres": successful_probe, "redis": failed_probe},
        timeout_seconds=0.1,
    )
    transport = ASGITransport(app=application)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/ready")

    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {
        "status": "unavailable",
        "checks": {"postgres": "ok", "redis": "unavailable"},
    }
    assert "dependency is unavailable" not in response.text


@pytest.mark.asyncio
async def test_readiness_enforces_probe_timeout() -> None:
    service = ReadinessService({"redis": slow_probe}, timeout_seconds=0.001)

    result = await service.check()

    assert result.ready is False
    assert result.checks == {"redis": False}


@pytest.mark.asyncio
async def test_redis_probe_uses_real_dependency_when_configured(
    monkeypatch: MonkeyPatch,
) -> None:
    redis_url = os.getenv("TEST_REDIS_URL")
    if redis_url is None:
        pytest.skip("TEST_REDIS_URL is not configured")
    monkeypatch.setenv("REDIS_URL", redis_url)
    get_settings.cache_clear()

    try:
        await probe_redis()
    finally:
        get_settings.cache_clear()
