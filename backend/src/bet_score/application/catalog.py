from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from bet_score.domain.catalog import EventProvenance, SportingEvent


class EventNotFoundError(Exception):
    def __init__(self, event_id: UUID) -> None:
        super().__init__(f"Матч {event_id} не найден")
        self.event_id = event_id


@dataclass(frozen=True, slots=True)
class EventQuery:
    starts_from: datetime
    limit: int = 20


class CatalogRepository(Protocol):
    async def list_events(self, query: EventQuery) -> tuple[SportingEvent, ...]: ...

    async def get_event(self, event_id: UUID) -> SportingEvent | None: ...

    async def list_event_provenance(self, event_id: UUID) -> tuple[EventProvenance, ...]: ...


class CatalogService:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    async def list_upcoming_events(
        self,
        *,
        starts_from: datetime | None = None,
        limit: int = 20,
    ) -> tuple[SportingEvent, ...]:
        normalized_start = starts_from or datetime.now(UTC)
        if normalized_start.tzinfo is None:
            normalized_start = normalized_start.replace(tzinfo=UTC)
        return await self._repository.list_events(
            EventQuery(starts_from=normalized_start, limit=min(max(limit, 1), 100))
        )

    async def get_event(self, event_id: UUID) -> SportingEvent:
        event = await self._repository.get_event(event_id)
        if event is None:
            raise EventNotFoundError(event_id)
        return event

    async def list_event_provenance(self, event_id: UUID) -> tuple[EventProvenance, ...]:
        if await self._repository.get_event(event_id) is None:
            raise EventNotFoundError(event_id)
        return await self._repository.list_event_provenance(event_id)
