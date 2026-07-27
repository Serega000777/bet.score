import asyncio
import os
from collections.abc import AsyncIterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from bet_score.application.live import (
    EventUpdated,
    LiveConnectionRegistry,
    LiveHeartbeat,
    stream_live_messages,
)
from bet_score.infrastructure.live import RedisEventUpdateBroker
from bet_score.main import create_app
from bet_score.presentation.api.dependencies import (
    get_catalog_service,
    get_event_update_subscriber,
)

EVENT_ID = UUID("70000000-0000-0000-0000-000000000001")


class FakeCatalogService:
    async def get_event(self, event_id: UUID) -> object:
        assert event_id == EVENT_ID
        return object()


class FakeSubscriber:
    async def subscribe(self, event_id: UUID) -> AsyncIterator[EventUpdated]:
        yield EventUpdated(event_id=event_id)


class BlockingSubscriber:
    async def subscribe(self, event_id: UUID) -> AsyncIterator[EventUpdated]:
        await asyncio.Event().wait()
        yield EventUpdated(event_id=event_id)


def test_live_stream_forwards_versioned_event_invalidation() -> None:
    application = create_app()
    application.dependency_overrides[get_catalog_service] = FakeCatalogService
    application.dependency_overrides[get_event_update_subscriber] = FakeSubscriber

    with (
        TestClient(application) as client,
        client.websocket_connect(
            f"/api/v1/live/events/{EVENT_ID}",
            headers={"Origin": "http://localhost:3001"},
        ) as websocket,
    ):
        assert websocket.receive_json() == {
            "type": "event.updated",
            "protocol_version": 1,
            "event_id": str(EVENT_ID),
        }
    assert "bet_score_live_connection_attempts_total 1" in (application.state.http_metrics.render())


def test_live_stream_rejects_untrusted_browser_origin() -> None:
    application = create_app()
    application.dependency_overrides[get_catalog_service] = FakeCatalogService
    application.dependency_overrides[get_event_update_subscriber] = FakeSubscriber

    with TestClient(application) as client:
        try:
            with client.websocket_connect(
                f"/api/v1/live/events/{EVENT_ID}",
                headers={"Origin": "https://attacker.example"},
            ):
                raise AssertionError("WebSocket must reject an untrusted origin")
        except WebSocketDisconnect as error:
            assert error.code == 4403


@pytest.mark.asyncio
async def test_redis_broker_delivers_event_update_when_configured() -> None:
    redis_url = os.getenv("TEST_REDIS_URL")
    if redis_url is None:
        pytest.skip("TEST_REDIS_URL is not configured")
    broker = RedisEventUpdateBroker(redis_url)
    subscription = broker.subscribe(EVENT_ID)
    received = asyncio.create_task(anext(subscription))
    await asyncio.sleep(0.05)

    try:
        await broker.publish(EventUpdated(event_id=EVENT_ID))
        assert await asyncio.wait_for(received, timeout=1) == EventUpdated(event_id=EVENT_ID)
    finally:
        received.cancel()
        await subscription.aclose()


@pytest.mark.asyncio
async def test_heartbeat_does_not_cancel_pending_subscription() -> None:
    messages = stream_live_messages(
        BlockingSubscriber(),
        EVENT_ID,
        heartbeat_seconds=0.001,
    )

    first = await anext(messages)
    second = await anext(messages)
    await messages.aclose()

    assert first == LiveHeartbeat()
    assert second == LiveHeartbeat()


@pytest.mark.asyncio
async def test_connection_registry_enforces_and_releases_limits() -> None:
    other_event_id = UUID("70000000-0000-0000-0000-000000000002")
    registry = LiveConnectionRegistry(total_limit=2, per_event_limit=1)

    assert await registry.try_acquire(EVENT_ID) is True
    assert await registry.try_acquire(EVENT_ID) is False
    assert await registry.try_acquire(other_event_id) is True
    assert await registry.try_acquire(UUID(int=3)) is False
    assert registry.total == 2

    await registry.release(EVENT_ID)

    assert registry.total == 1
    assert await registry.try_acquire(EVENT_ID) is True
