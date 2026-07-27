import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ValidationError
from redis.asyncio import Redis

from bet_score.application.live import EventUpdated

_CHANNEL_PREFIX = "bet-score:event:"


class _EventUpdatedPayload(BaseModel):
    type: str
    protocol_version: int
    event_id: UUID


class RedisEventUpdateBroker:
    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url

    async def publish(self, update: EventUpdated) -> None:
        client = Redis.from_url(self._redis_url)
        try:
            await client.publish(
                _channel(update.event_id),
                json.dumps(
                    {
                        "type": update.type,
                        "protocol_version": update.protocol_version,
                        "event_id": str(update.event_id),
                    },
                    separators=(",", ":"),
                ),
            )
        finally:
            await client.aclose()

    @asynccontextmanager
    async def _subscription(self, event_id: UUID) -> AsyncIterator[Any]:
        client = Redis.from_url(self._redis_url)
        pubsub = client.pubsub()
        try:
            await pubsub.subscribe(_channel(event_id))
            yield pubsub
        finally:
            await pubsub.unsubscribe(_channel(event_id))
            await pubsub.aclose()
            await client.aclose()

    async def subscribe(self, event_id: UUID) -> AsyncIterator[EventUpdated]:
        async with self._subscription(event_id) as pubsub:
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                update = _parse_update(message.get("data"))
                if update is not None and update.event_id == event_id:
                    yield update


def _channel(event_id: UUID) -> str:
    return f"{_CHANNEL_PREFIX}{event_id}"


def _parse_update(raw: object) -> EventUpdated | None:
    if not isinstance(raw, bytes):
        return None
    try:
        payload = _EventUpdatedPayload.model_validate_json(raw)
    except ValidationError:
        return None
    if payload.type != "event.updated" or payload.protocol_version != 1:
        return None
    return EventUpdated(event_id=payload.event_id)
