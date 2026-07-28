from datetime import UTC, datetime
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from bet_score.application.catalog import CatalogService, EventQuery
from bet_score.domain.catalog import (
    CompetitionSummary,
    EventProvenance,
    EventStatus,
    Participant,
    ParticipantRole,
    SportingEvent,
    SportSummary,
)
from bet_score.main import create_app
from bet_score.presentation.api.dependencies import get_catalog_service

EVENT_ID = UUID("40000000-0000-0000-0000-000000000001")


def make_event() -> SportingEvent:
    return SportingEvent(
        id=EVENT_ID,
        sport_code="football",
        sport_name="Футбол",
        competition_id=UUID("20000000-0000-0000-0000-000000000001"),
        competition_name="Тестовая лига",
        country_code="RU",
        starts_at=datetime(2026, 8, 1, 16, tzinfo=UTC),
        status=EventStatus.SCHEDULED,
        participants=(
            Participant(
                id=UUID("30000000-0000-0000-0000-000000000001"),
                name="Север",
                short_name="SEV",
                role=ParticipantRole.HOME,
            ),
            Participant(
                id=UUID("30000000-0000-0000-0000-000000000002"),
                name="Восток",
                short_name="VOS",
                role=ParticipantRole.AWAY,
            ),
        ),
    )


class FakeCatalogRepository:
    def __init__(self, events: tuple[SportingEvent, ...]) -> None:
        self.events = events
        self.last_query: EventQuery | None = None

    async def list_events(self, query: EventQuery) -> tuple[SportingEvent, ...]:
        self.last_query = query
        return self.events[: query.limit]

    async def get_event(self, event_id: UUID) -> SportingEvent | None:
        return next((event for event in self.events if event.id == event_id), None)

    async def list_event_provenance(self, event_id: UUID) -> tuple[EventProvenance, ...]:
        return (
            EventProvenance(
                provider_key="test-provider",
                version="v1",
                observed_at=datetime(2026, 8, 1, 15, tzinfo=UTC),
                ingested_at=datetime(2026, 8, 1, 15, 1, tzinfo=UTC),
                checksum="a" * 64,
            ),
        )

    async def list_sports(self, starts_from: datetime) -> tuple[SportSummary, ...]:
        return (SportSummary(code="football", name="Футбол", event_count=len(self.events)),)

    async def list_competitions(
        self,
        starts_from: datetime,
        sport_code: str | None,
    ) -> tuple[CompetitionSummary, ...]:
        return (
            CompetitionSummary(
                id=make_event().competition_id,
                sport_code="football",
                name="Тестовая лига",
                country_code="RU",
                event_count=len(self.events),
            ),
        )


@pytest.mark.asyncio
async def test_catalog_service_limits_page_size() -> None:
    repository = FakeCatalogRepository((make_event(),))
    service = CatalogService(repository)

    await service.list_upcoming_events(limit=500)

    assert repository.last_query is not None
    assert repository.last_query.limit == 100


@pytest.mark.asyncio
async def test_events_api_returns_canonical_match() -> None:
    application = create_app()
    application.dependency_overrides[get_catalog_service] = lambda: CatalogService(
        FakeCatalogRepository((make_event(),))
    )

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/events")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["sport_code"] == "football"
    assert payload["items"][0]["home"]["name"] == "Север"
    assert payload["items"][0]["away"]["name"] == "Восток"


@pytest.mark.asyncio
async def test_events_api_forwards_canonical_filters() -> None:
    repository = FakeCatalogRepository((make_event(),))
    application = create_app()
    application.dependency_overrides[get_catalog_service] = lambda: CatalogService(repository)
    competition_id = make_event().competition_id

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/events",
            params={"sport_code": "football", "competition_id": str(competition_id)},
        )

    assert response.status_code == 200
    assert repository.last_query is not None
    assert repository.last_query.sport_code == "football"
    assert repository.last_query.competition_id == competition_id


@pytest.mark.asyncio
async def test_catalog_navigation_api_returns_counts() -> None:
    application = create_app()
    application.dependency_overrides[get_catalog_service] = lambda: CatalogService(
        FakeCatalogRepository((make_event(),))
    )
    transport = ASGITransport(app=application)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sports = await client.get("/api/v1/sports")
        competitions = await client.get(
            "/api/v1/competitions",
            params={"sport_code": "football"},
        )

    assert sports.json()["items"][0] == {
        "code": "football",
        "name": "Футбол",
        "event_count": 1,
    }
    assert competitions.json()["items"][0]["sport_code"] == "football"
    assert competitions.json()["items"][0]["event_count"] == 1


@pytest.mark.asyncio
async def test_event_api_returns_structured_not_found_error() -> None:
    application = create_app()
    application.dependency_overrides[get_catalog_service] = lambda: CatalogService(
        FakeCatalogRepository(())
    )

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/events/{EVENT_ID}")

    assert response.status_code == 404
    assert response.json()["code"] == "event_not_found"


@pytest.mark.asyncio
async def test_event_provenance_api_excludes_raw_provider_payload() -> None:
    application = create_app()
    application.dependency_overrides[get_catalog_service] = lambda: CatalogService(
        FakeCatalogRepository((make_event(),))
    )

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/events/{EVENT_ID}/provenance")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["provider_key"] == "test-provider"
    assert payload["items"][0]["checksum"] == "a" * 64
    assert "payload" not in payload["items"][0]
    assert "external_id" not in payload["items"][0]
