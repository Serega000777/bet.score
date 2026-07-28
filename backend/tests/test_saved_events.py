from datetime import UTC, datetime
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from bet_score.application.catalog import EventQuery
from bet_score.application.saved_events import SavedEventsService
from bet_score.domain.catalog import (
    CompetitionSummary,
    EventProvenance,
    EventStatus,
    Participant,
    ParticipantRole,
    SportingEvent,
    SportSummary,
)
from bet_score.domain.identity import User
from bet_score.main import create_app
from bet_score.presentation.api.dependencies import (
    get_current_user,
    get_saved_events_service,
)

USER_ID = UUID("50000000-0000-0000-0000-000000000001")
EVENT_ID = UUID("70000000-0000-0000-0000-000000000001")
COMPETITION_ID = UUID("70000000-0000-0000-0000-000000000002")
USER = User(id=USER_ID, display_name="Иван", username="ivan", locale="ru")


def make_event() -> SportingEvent:
    return SportingEvent(
        id=EVENT_ID,
        sport_code="football",
        sport_name="Футбол",
        competition_id=COMPETITION_ID,
        competition_name="Премьер-лига",
        country_code="RU",
        starts_at=datetime(2026, 8, 1, 17, tzinfo=UTC),
        status=EventStatus.SCHEDULED,
        participants=(
            Participant(
                id=UUID("70000000-0000-0000-0000-000000000003"),
                name="Север",
                short_name="SEV",
                role=ParticipantRole.HOME,
                score=None,
            ),
            Participant(
                id=UUID("70000000-0000-0000-0000-000000000004"),
                name="Восток",
                short_name="VOS",
                role=ParticipantRole.AWAY,
                score=None,
            ),
        ),
    )


class FakeSavedEventRepository:
    def __init__(self) -> None:
        self.event_ids: list[UUID] = []

    async def list_event_ids(self, user_id: UUID, limit: int) -> tuple[UUID, ...]:
        assert user_id == USER_ID
        return tuple(self.event_ids[:limit])

    async def add(self, user_id: UUID, event_id: UUID) -> None:
        assert user_id == USER_ID
        if event_id not in self.event_ids:
            self.event_ids.insert(0, event_id)

    async def remove(self, user_id: UUID, event_id: UUID) -> None:
        assert user_id == USER_ID
        if event_id in self.event_ids:
            self.event_ids.remove(event_id)


class FakeCatalogRepository:
    async def list_events(self, query: EventQuery) -> tuple[SportingEvent, ...]:
        return ()

    async def get_event(self, event_id: UUID) -> SportingEvent | None:
        return make_event() if event_id == EVENT_ID else None

    async def list_event_provenance(self, event_id: UUID) -> tuple[EventProvenance, ...]:
        return ()

    async def list_sports(self, starts_from: datetime) -> tuple[SportSummary, ...]:
        return ()

    async def list_competitions(
        self,
        starts_from: datetime,
        sport_code: str | None,
    ) -> tuple[CompetitionSummary, ...]:
        return ()


@pytest.mark.asyncio
async def test_saved_events_api_is_idempotent() -> None:
    repository = FakeSavedEventRepository()
    service = SavedEventsService(repository, FakeCatalogRepository())
    application = create_app()
    application.dependency_overrides[get_current_user] = lambda: USER
    application.dependency_overrides[get_saved_events_service] = lambda: service

    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://test",
    ) as client:
        first = await client.put(f"/api/v1/saved-events/{EVENT_ID}")
        repeated = await client.put(f"/api/v1/saved-events/{EVENT_ID}")
        listed = await client.get("/api/v1/saved-events")
        removed = await client.delete(f"/api/v1/saved-events/{EVENT_ID}")
        empty = await client.get("/api/v1/saved-events")

    assert first.status_code == 204
    assert repeated.status_code == 204
    assert listed.json()["items"][0]["id"] == str(EVENT_ID)
    assert listed.json()["count"] == 1
    assert removed.status_code == 204
    assert empty.json()["count"] == 0


@pytest.mark.asyncio
async def test_saved_events_api_rejects_unknown_event() -> None:
    service = SavedEventsService(FakeSavedEventRepository(), FakeCatalogRepository())
    application = create_app()
    application.dependency_overrides[get_current_user] = lambda: USER
    application.dependency_overrides[get_saved_events_service] = lambda: service
    unknown_id = UUID("70000000-0000-0000-0000-000000000099")

    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://test",
    ) as client:
        response = await client.put(f"/api/v1/saved-events/{unknown_id}")

    assert response.status_code == 404
    assert response.json()["code"] == "event_not_found"
