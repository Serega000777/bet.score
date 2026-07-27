from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from bet_score.application.live import EventUpdated, EventUpdatePublisher


@dataclass(frozen=True, slots=True)
class OutboxMessage:
    id: int
    event_id: UUID
    attempts: int


class OutboxRepository(Protocol):
    async def claim(self, *, batch_size: int, lease_seconds: float) -> list[OutboxMessage]: ...

    async def mark_delivered(self, message_id: int) -> None: ...

    async def mark_failed(self, message_id: int, *, retry_seconds: float) -> None: ...


class OutboxDispatcher:
    def __init__(self, repository: OutboxRepository, publisher: EventUpdatePublisher) -> None:
        self._repository = repository
        self._publisher = publisher

    async def run_once(self, *, batch_size: int, lease_seconds: float) -> int:
        messages = await self._repository.claim(
            batch_size=batch_size,
            lease_seconds=lease_seconds,
        )
        delivered = 0
        for message in messages:
            try:
                await self._publisher.publish(EventUpdated(event_id=message.event_id))
            except Exception:
                await self._repository.mark_failed(
                    message.id,
                    retry_seconds=min(2 ** min(message.attempts, 9), 300),
                )
                continue
            await self._repository.mark_delivered(message.id)
            delivered += 1
        return delivered
