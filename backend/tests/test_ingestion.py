from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest

from bet_score.application.ingestion import EventIngestionService, IngestionResult
from bet_score.domain.catalog import EventStatus
from bet_score.domain.ingestion import ProviderCompetition, ProviderEvent, ProviderTeam

EVENT_ID = UUID("60000000-0000-0000-0000-000000000001")


def provider_event(**changes: object) -> ProviderEvent:
    values: dict[str, object] = {
        "provider_key": "demo-provider",
        "external_id": "match-42",
        "version": "2026-07-25T09:00:00Z",
        "observed_at": datetime.now(UTC),
        "sport_code": "football",
        "sport_name": "Футбол",
        "competition": ProviderCompetition("league-1", "Премьер-лига", "RU"),
        "starts_at": datetime(2026, 7, 26, 17, 0, tzinfo=UTC),
        "status": EventStatus.SCHEDULED,
        "home": ProviderTeam("team-1", "Север", "SEV", "RU"),
        "away": ProviderTeam("team-2", "Восток", "VOS", "RU"),
    }
    values.update(changes)
    return ProviderEvent(**values)  # type: ignore[arg-type]


class FakeIngestionRepository:
    def __init__(self) -> None:
        self.checksums: list[str] = []

    async def ingest(
        self,
        event: ProviderEvent,
        *,
        payload: dict[str, Any],
        checksum: str,
    ) -> IngestionResult:
        assert event.external_id == "match-42"
        assert payload["status"] == "scheduled"
        self.checksums.append(checksum)
        return IngestionResult(EVENT_ID, snapshot_created=len(self.checksums) == 1)


@pytest.mark.asyncio
async def test_ingestion_checksum_is_stable_for_key_order() -> None:
    repository = FakeIngestionRepository()
    service = EventIngestionService(repository)

    first = await service.ingest(
        provider_event(),
        payload={"status": "scheduled", "score": {"home": None, "away": None}},
    )
    second = await service.ingest(
        provider_event(),
        payload={"score": {"away": None, "home": None}, "status": "scheduled"},
    )

    assert first.snapshot_created is True
    assert second.snapshot_created is False
    assert repository.checksums[0] == repository.checksums[1]


@pytest.mark.asyncio
async def test_ingestion_rejects_oversized_payload() -> None:
    service = EventIngestionService(FakeIngestionRepository())

    with pytest.raises(ValueError, match="размер"):
        await service.ingest(provider_event(), payload={"raw": "x" * 1_000_001})


def test_provider_event_rejects_same_team_on_both_sides() -> None:
    team = ProviderTeam("team-1", "Север", "SEV")

    with pytest.raises(ValueError, match="разными"):
        provider_event(home=team, away=team)


def test_provider_event_rejects_negative_score() -> None:
    with pytest.raises(ValueError, match="отрицательным"):
        provider_event(home_score=-1)


def test_provider_entity_rejects_invalid_country_code() -> None:
    with pytest.raises(ValueError, match="ISO 3166"):
        ProviderTeam("team-1", "Север", "SEV", "rus")
