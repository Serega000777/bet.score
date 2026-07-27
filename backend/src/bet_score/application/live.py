from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class EventUpdated:
    event_id: UUID
    type: str = "event.updated"
    protocol_version: int = 1


class EventUpdatePublisher(Protocol):
    async def publish(self, update: EventUpdated) -> None: ...


class EventUpdateSubscriber(Protocol):
    def subscribe(self, event_id: UUID) -> AsyncIterator[EventUpdated]: ...
