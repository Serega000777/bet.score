import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from bet_score.application.catalog import CatalogService
from bet_score.application.ingestion import (
    EventIngestionService,
    IngestionConflictError,
)
from bet_score.domain.catalog import EventStatus
from bet_score.domain.ingestion import ProviderCompetition, ProviderEvent, ProviderTeam
from bet_score.infrastructure.catalog_repository import SqlAlchemyCatalogRepository
from bet_score.infrastructure.ingestion_repository import SqlAlchemyEventIngestionRepository
from bet_score.infrastructure.outbox_repository import SqlAlchemyOutboxRepository
from bet_score.infrastructure.outbox_stats import SqlAlchemyOutboxStatsReader

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.mark.asyncio
@pytest.mark.skipif(TEST_DATABASE_URL is None, reason="Нужна тестовая PostgreSQL")
async def test_postgres_ingestion_is_idempotent_and_preserves_provenance() -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL)
    provider_key = f"integration-{uuid4()}"
    event = ProviderEvent(
        provider_key=provider_key,
        external_id="match-42",
        version="v1",
        observed_at=datetime.now(UTC),
        sport_code="football",
        sport_name="Футбол",
        competition=ProviderCompetition("league-1", "Тестовая лига", "RU"),
        starts_at=datetime(2026, 8, 1, 17, 0, tzinfo=UTC),
        status=EventStatus.SCHEDULED,
        home=ProviderTeam("home-1", "Север", "SEV", "RU"),
        away=ProviderTeam("away-1", "Восток", "VOS", "RU"),
    )
    payload = {"id": "match-42", "status": "scheduled"}

    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            service = EventIngestionService(SqlAlchemyEventIngestionRepository(session))
            first = await service.ingest(event, payload=payload)
            repeated = await service.ingest(event, payload=payload)

            assert first.snapshot_created is True
            assert repeated == first.__class__(first.event_id, snapshot_created=False)

            with pytest.raises(IngestionConflictError, match="изменил payload"):
                await service.ingest(event, payload={**payload, "status": "live"})

            updated_event = replace(
                event,
                version="v2",
                status=EventStatus.LIVE,
                home_score=1,
                away_score=0,
            )
            updated = await service.ingest(
                updated_event,
                payload={"id": "match-42", "status": "live", "score": [1, 0]},
            )
            assert updated.event_id == first.event_id
            assert updated.snapshot_created is True

            stale_event = replace(
                event,
                version="delayed-v0",
                observed_at=event.observed_at - timedelta(hours=1),
            )
            stale = await service.ingest(
                stale_event,
                payload={"id": "match-42", "status": "scheduled", "delayed": True},
            )
            assert stale.event_id == first.event_id
            assert stale.snapshot_created is True

        async with engine.connect() as connection:
            row = (
                await connection.execute(
                    text(
                        """
                        SELECT
                          count(DISTINCT s.id) AS snapshots,
                          count(DISTINCT o.id) AS outbox_messages,
                          min(s.checksum) AS checksum,
                          min(e.status) AS status,
                          max(ep.score) FILTER (WHERE ep.role = 'home') AS home_score
                        FROM provider_event_snapshot s
                        JOIN data_provider p ON p.id = s.provider_id
                        JOIN sporting_event e ON e.id = s.event_id
                        JOIN event_participant ep ON ep.event_id = e.id
                        JOIN event_outbox o ON o.source_snapshot_id = s.id
                        WHERE p.key = :provider_key
                        """
                    ),
                    {"provider_key": provider_key},
                )
            ).one()
            assert row.snapshots == 3
            assert row.outbox_messages == 3
            assert len(row.checksum) == 64
            assert row.status == "live"
            assert row.home_score == 1

        with pytest.raises(DBAPIError, match="immutable"):
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        """
                        UPDATE provider_event_snapshot s
                        SET checksum = repeat('0', 64)
                        FROM data_provider p
                        WHERE p.id = s.provider_id AND p.key = :provider_key
                        """
                    ),
                    {"provider_key": provider_key},
                )

        async with AsyncSession(engine, expire_on_commit=False) as session:
            sources = await CatalogService(
                SqlAlchemyCatalogRepository(session)
            ).list_event_provenance(first.event_id)

        assert [source.version for source in sources] == ["v2", "v1", "delayed-v0"]
        assert all(source.provider_key == provider_key for source in sources)

        outbox = SqlAlchemyOutboxRepository(engine)
        claimed = await outbox.claim(batch_size=100, lease_seconds=30)
        event_messages = [message for message in claimed if message.event_id == first.event_id]
        assert len(event_messages) == 3
        assert all(message.attempts == 1 for message in event_messages)

        await outbox.mark_delivered(event_messages[0].id)
        await outbox.mark_failed(event_messages[1].id, retry_seconds=2)
        async with engine.connect() as connection:
            states = (
                await connection.execute(
                    text(
                        """
                        SELECT delivered_at IS NOT NULL AS delivered, last_error_code
                        FROM event_outbox
                        WHERE id IN (:delivered_id, :failed_id)
                        ORDER BY id
                        """
                    ),
                    {
                        "delivered_id": event_messages[0].id,
                        "failed_id": event_messages[1].id,
                    },
                )
            ).all()
        assert any(row.delivered for row in states)
        assert any(row.last_error_code == "publish_failed" for row in states)

        async with AsyncSession(engine, expire_on_commit=False) as session:
            stats = await SqlAlchemyOutboxStatsReader(session).get_stats()
        assert stats.pending >= 2
        assert stats.oldest_pending_seconds >= 0
        assert stats.delivered >= 1
        assert stats.retries >= 1
    finally:
        await engine.dispose()
