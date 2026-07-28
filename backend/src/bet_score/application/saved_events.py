from typing import Protocol
from uuid import UUID

from bet_score.application.catalog import CatalogRepository
from bet_score.domain.catalog import SportingEvent


class SavedEventRepository(Protocol):
    async def list_event_ids(self, user_id: UUID, limit: int) -> tuple[UUID, ...]: ...

    async def add(self, user_id: UUID, event_id: UUID) -> None: ...

    async def remove(self, user_id: UUID, event_id: UUID) -> None: ...

    async def contains(self, user_id: UUID, event_id: UUID) -> bool: ...


class SavedEventNotFoundError(Exception):
    pass


class SavedEventsService:
    def __init__(
        self,
        repository: SavedEventRepository,
        catalog: CatalogRepository,
    ) -> None:
        self._repository = repository
        self._catalog = catalog

    async def list_events(self, user_id: UUID, *, limit: int = 50) -> tuple[SportingEvent, ...]:
        events: list[SportingEvent] = []
        for event_id in await self._repository.list_event_ids(
            user_id,
            min(max(limit, 1), 100),
        ):
            event = await self._catalog.get_event(event_id)
            if event is not None:
                events.append(event)
        return tuple(events)

    async def save(self, user_id: UUID, event_id: UUID) -> None:
        if await self._catalog.get_event(event_id) is None:
            raise SavedEventNotFoundError
        await self._repository.add(user_id, event_id)

    async def remove(self, user_id: UUID, event_id: UUID) -> None:
        await self._repository.remove(user_id, event_id)

    async def contains(self, user_id: UUID, event_id: UUID) -> bool:
        return await self._repository.contains(user_id, event_id)
