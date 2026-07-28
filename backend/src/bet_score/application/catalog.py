from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from bet_score.domain.catalog import (
    CompetitionSummary,
    EventProvenance,
    SportingEvent,
    SportSummary,
)


class EventNotFoundError(Exception):
    def __init__(self, event_id: UUID) -> None:
        super().__init__(f"Матч {event_id} не найден")
        self.event_id = event_id


@dataclass(frozen=True, slots=True)
class EventQuery:
    starts_from: datetime
    limit: int = 20
    sport_code: str | None = None
    competition_id: UUID | None = None


class CatalogRepository(Protocol):
    async def list_events(self, query: EventQuery) -> tuple[SportingEvent, ...]: ...

    async def get_event(self, event_id: UUID) -> SportingEvent | None: ...

    async def list_event_provenance(self, event_id: UUID) -> tuple[EventProvenance, ...]: ...

    async def list_sports(self, starts_from: datetime) -> tuple[SportSummary, ...]: ...

    async def list_competitions(
        self,
        starts_from: datetime,
        sport_code: str | None,
    ) -> tuple[CompetitionSummary, ...]: ...


class CatalogService:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    async def list_upcoming_events(
        self,
        *,
        starts_from: datetime | None = None,
        limit: int = 20,
        sport_code: str | None = None,
        competition_id: UUID | None = None,
    ) -> tuple[SportingEvent, ...]:
        normalized_start = starts_from or datetime.now(UTC)
        if normalized_start.tzinfo is None:
            normalized_start = normalized_start.replace(tzinfo=UTC)
        return await self._repository.list_events(
            EventQuery(
                starts_from=normalized_start,
                limit=min(max(limit, 1), 100),
                sport_code=sport_code,
                competition_id=competition_id,
            )
        )

    async def list_sports(
        self,
        *,
        starts_from: datetime | None = None,
    ) -> tuple[SportSummary, ...]:
        return await self._repository.list_sports(self._normalize_start(starts_from))

    async def list_competitions(
        self,
        *,
        starts_from: datetime | None = None,
        sport_code: str | None = None,
    ) -> tuple[CompetitionSummary, ...]:
        return await self._repository.list_competitions(
            self._normalize_start(starts_from),
            sport_code,
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

    @staticmethod
    def _normalize_start(value: datetime | None) -> datetime:
        result = value or datetime.now(UTC)
        return result.replace(tzinfo=UTC) if result.tzinfo is None else result
