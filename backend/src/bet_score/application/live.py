import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class EventUpdated:
    event_id: UUID
    type: str = "event.updated"
    protocol_version: int = 1


@dataclass(frozen=True, slots=True)
class LiveHeartbeat:
    type: str = "heartbeat"
    protocol_version: int = 1


class EventUpdatePublisher(Protocol):
    async def publish(self, update: EventUpdated) -> None: ...


class EventUpdateSubscriber(Protocol):
    def subscribe(self, event_id: UUID) -> AsyncIterator[EventUpdated]: ...


class LiveConnectionRegistry:
    def __init__(self, *, total_limit: int, per_event_limit: int) -> None:
        self._total_limit = total_limit
        self._per_event_limit = per_event_limit
        self._total = 0
        self._by_event: dict[UUID, int] = {}
        self._lock = asyncio.Lock()

    async def try_acquire(self, event_id: UUID) -> bool:
        async with self._lock:
            event_count = self._by_event.get(event_id, 0)
            if self._total >= self._total_limit or event_count >= self._per_event_limit:
                return False
            self._total += 1
            self._by_event[event_id] = event_count + 1
            return True

    async def release(self, event_id: UUID) -> None:
        async with self._lock:
            event_count = self._by_event.get(event_id, 0)
            if event_count == 0:
                return
            self._total -= 1
            if event_count == 1:
                self._by_event.pop(event_id)
            else:
                self._by_event[event_id] = event_count - 1

    @property
    def total(self) -> int:
        return self._total


async def stream_live_messages(
    subscriber: EventUpdateSubscriber,
    event_id: UUID,
    *,
    heartbeat_seconds: float,
) -> AsyncIterator[EventUpdated | LiveHeartbeat]:
    updates = subscriber.subscribe(event_id)
    pending: asyncio.Future[EventUpdated] = asyncio.ensure_future(anext(updates))
    try:
        while True:
            done, _ = await asyncio.wait({pending}, timeout=heartbeat_seconds)
            if not done:
                yield LiveHeartbeat()
                continue
            try:
                yield pending.result()
            except StopAsyncIteration:
                return
            pending = asyncio.ensure_future(anext(updates))
    finally:
        pending.cancel()
        with suppress(asyncio.CancelledError, StopAsyncIteration):
            await pending
