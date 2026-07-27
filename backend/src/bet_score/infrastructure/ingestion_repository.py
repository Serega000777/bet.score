import json
from typing import Any, cast
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from bet_score.application.ingestion import IngestionConflictError, IngestionResult
from bet_score.domain.ingestion import ProviderCompetition, ProviderEvent, ProviderTeam


class SqlAlchemyEventIngestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ingest(
        self,
        event: ProviderEvent,
        *,
        payload: dict[str, Any],
        checksum: str,
    ) -> IngestionResult:
        async with self._session.begin():
            await self._session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
                {"key": event.provider_key},
            )
            provider_id = await self._provider_id(event.provider_key)
            existing = (
                await self._session.execute(
                    text(
                        """
                        SELECT event_id, checksum
                        FROM provider_event_snapshot
                        WHERE provider_id = :provider_id
                          AND external_event_id = :external_id
                          AND version = :version
                        """
                    ),
                    {
                        "provider_id": provider_id,
                        "external_id": event.external_id,
                        "version": event.version,
                    },
                )
            ).one_or_none()
            if existing is not None:
                if existing.checksum != checksum:
                    raise IngestionConflictError(
                        "Поставщик изменил payload уже обработанной версии события"
                    )
                return IngestionResult(event_id=existing.event_id, snapshot_created=False)

            latest = (
                await self._session.execute(
                    text(
                        """
                        SELECT event_id, observed_at
                        FROM provider_event_snapshot
                        WHERE provider_id = :provider_id
                          AND external_event_id = :external_id
                        ORDER BY observed_at DESC, ingested_at DESC
                        LIMIT 1
                        """
                    ),
                    {"provider_id": provider_id, "external_id": event.external_id},
                )
            ).one_or_none()
            if latest is not None and event.observed_at < latest.observed_at:
                snapshot_id = await self._insert_snapshot(
                    provider_id,
                    latest.event_id,
                    event,
                    payload,
                    checksum,
                )
                await self._enqueue_event_update(snapshot_id, latest.event_id)
                return IngestionResult(event_id=latest.event_id, snapshot_created=True)

            sport_id = await self._sport_id(event.sport_code, event.sport_name)
            competition_id = await self._competition_id(
                provider_id,
                sport_id,
                event.competition,
            )
            home_id = await self._team_id(provider_id, sport_id, event.home)
            away_id = await self._team_id(provider_id, sport_id, event.away)
            event_id = await self._event_id(provider_id, competition_id, event)
            await self._replace_participants(event_id, home_id, away_id, event)
            snapshot_id = await self._insert_snapshot(
                provider_id,
                event_id,
                event,
                payload,
                checksum,
            )
            await self._enqueue_event_update(snapshot_id, event_id)
            return IngestionResult(event_id=event_id, snapshot_created=True)

    async def _insert_snapshot(
        self,
        provider_id: UUID,
        event_id: UUID,
        event: ProviderEvent,
        payload: dict[str, Any],
        checksum: str,
    ) -> UUID:
        return cast(
            UUID,
            (
                await self._session.execute(
                    text(
                        """
                        INSERT INTO provider_event_snapshot(
                          provider_id, external_event_id, event_id, version,
                          observed_at, checksum, payload
                        )
                        VALUES(
                          :provider_id, :external_id, :event_id, :version,
                          :observed_at, :checksum, CAST(:payload AS jsonb)
                        )
                        RETURNING id
                        """
                    ),
                    {
                        "provider_id": provider_id,
                        "external_id": event.external_id,
                        "event_id": event_id,
                        "version": event.version,
                        "observed_at": event.observed_at,
                        "checksum": checksum,
                        "payload": json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    },
                )
            ).scalar_one(),
        )

    async def _enqueue_event_update(self, snapshot_id: UUID, event_id: UUID) -> None:
        await self._session.execute(
            text(
                """
                INSERT INTO event_outbox(
                  source_snapshot_id, event_id, event_type, protocol_version
                )
                VALUES(:snapshot_id, :event_id, 'event.updated', 1)
                """
            ),
            {
                "snapshot_id": snapshot_id,
                "event_id": event_id,
            },
        )

    async def _provider_id(self, provider_key: str) -> UUID:
        return cast(
            UUID,
            (
                await self._session.execute(
                    text(
                        """
                        INSERT INTO data_provider(key, name)
                        VALUES(:key, :key)
                        ON CONFLICT (key) DO UPDATE SET name = data_provider.name
                        RETURNING id
                        """
                    ),
                    {"key": provider_key},
                )
            ).scalar_one(),
        )

    async def _sport_id(self, code: str, name: str) -> UUID:
        return cast(
            UUID,
            (
                await self._session.execute(
                    text(
                        """
                        INSERT INTO sport(code, name)
                        VALUES(:code, :name)
                        ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id
                        """
                    ),
                    {"code": code, "name": name},
                )
            ).scalar_one(),
        )

    async def _competition_id(
        self,
        provider_id: UUID,
        sport_id: UUID,
        competition: ProviderCompetition,
    ) -> UUID:
        mapped_id = (
            await self._session.execute(
                text(
                    """
                    SELECT competition_id FROM provider_competition
                    WHERE provider_id = :provider_id AND external_id = :external_id
                    """
                ),
                {"provider_id": provider_id, "external_id": competition.external_id},
            )
        ).scalar_one_or_none()
        if mapped_id is None:
            mapped_id = (
                await self._session.execute(
                    text(
                        """
                        INSERT INTO competition(sport_id, name, country_code)
                        VALUES(:sport_id, :name, :country_code)
                        ON CONFLICT (sport_id, name, country_code)
                        DO UPDATE SET name = EXCLUDED.name
                        RETURNING id
                        """
                    ),
                    {
                        "sport_id": sport_id,
                        "name": competition.name,
                        "country_code": competition.country_code,
                    },
                )
            ).scalar_one()
            await self._session.execute(
                text(
                    """
                    INSERT INTO provider_competition(provider_id, external_id, competition_id)
                    VALUES(:provider_id, :external_id, :canonical_id)
                    """
                ),
                {
                    "provider_id": provider_id,
                    "external_id": competition.external_id,
                    "canonical_id": mapped_id,
                },
            )
        else:
            await self._session.execute(
                text(
                    """
                    UPDATE competition SET name = :name, country_code = :country_code
                    WHERE id = :canonical_id
                    """
                ),
                {
                    "canonical_id": mapped_id,
                    "name": competition.name,
                    "country_code": competition.country_code,
                },
            )
        return cast(UUID, mapped_id)

    async def _team_id(
        self,
        provider_id: UUID,
        sport_id: UUID,
        team: ProviderTeam,
    ) -> UUID:
        mapped_id = (
            await self._session.execute(
                text(
                    """
                    SELECT team_id FROM provider_team
                    WHERE provider_id = :provider_id AND external_id = :external_id
                    """
                ),
                {"provider_id": provider_id, "external_id": team.external_id},
            )
        ).scalar_one_or_none()
        if mapped_id is None:
            mapped_id = (
                await self._session.execute(
                    text(
                        """
                        INSERT INTO team(sport_id, name, short_name, country_code)
                        VALUES(:sport_id, :name, :short_name, :country_code)
                        ON CONFLICT (sport_id, name)
                        DO UPDATE SET
                          short_name = EXCLUDED.short_name,
                          country_code = EXCLUDED.country_code
                        RETURNING id
                        """
                    ),
                    {
                        "sport_id": sport_id,
                        "name": team.name,
                        "short_name": team.short_name,
                        "country_code": team.country_code,
                    },
                )
            ).scalar_one()
            await self._session.execute(
                text(
                    """
                    INSERT INTO provider_team(provider_id, external_id, team_id)
                    VALUES(:provider_id, :external_id, :canonical_id)
                    """
                ),
                {
                    "provider_id": provider_id,
                    "external_id": team.external_id,
                    "canonical_id": mapped_id,
                },
            )
        else:
            await self._session.execute(
                text(
                    """
                    UPDATE team
                    SET name = :name, short_name = :short_name, country_code = :country_code
                    WHERE id = :canonical_id
                    """
                ),
                {
                    "canonical_id": mapped_id,
                    "name": team.name,
                    "short_name": team.short_name,
                    "country_code": team.country_code,
                },
            )
        return cast(UUID, mapped_id)

    async def _event_id(
        self,
        provider_id: UUID,
        competition_id: UUID,
        event: ProviderEvent,
    ) -> UUID:
        mapped_id = (
            await self._session.execute(
                text(
                    """
                    SELECT event_id FROM provider_event
                    WHERE provider_id = :provider_id AND external_id = :external_id
                    """
                ),
                {"provider_id": provider_id, "external_id": event.external_id},
            )
        ).scalar_one_or_none()
        if mapped_id is None:
            mapped_id = (
                await self._session.execute(
                    text(
                        """
                        INSERT INTO sporting_event(competition_id, starts_at, status)
                        VALUES(:competition_id, :starts_at, :status)
                        RETURNING id
                        """
                    ),
                    {
                        "competition_id": competition_id,
                        "starts_at": event.starts_at,
                        "status": event.status.value,
                    },
                )
            ).scalar_one()
            await self._session.execute(
                text(
                    """
                    INSERT INTO provider_event(provider_id, external_id, event_id)
                    VALUES(:provider_id, :external_id, :canonical_id)
                    """
                ),
                {
                    "provider_id": provider_id,
                    "external_id": event.external_id,
                    "canonical_id": mapped_id,
                },
            )
        else:
            await self._session.execute(
                text(
                    """
                    UPDATE sporting_event
                    SET competition_id = :competition_id,
                        starts_at = :starts_at,
                        status = :status,
                        updated_at = now()
                    WHERE id = :canonical_id
                    """
                ),
                {
                    "canonical_id": mapped_id,
                    "competition_id": competition_id,
                    "starts_at": event.starts_at,
                    "status": event.status.value,
                },
            )
        return cast(UUID, mapped_id)

    async def _replace_participants(
        self,
        event_id: UUID,
        home_id: UUID,
        away_id: UUID,
        event: ProviderEvent,
    ) -> None:
        await self._session.execute(
            text("DELETE FROM event_participant WHERE event_id = :event_id"),
            {"event_id": event_id},
        )
        await self._session.execute(
            text(
                """
                INSERT INTO event_participant(event_id, team_id, role, score)
                VALUES
                  (:event_id, :home_id, 'home', :home_score),
                  (:event_id, :away_id, 'away', :away_score)
                """
            ),
            {
                "event_id": event_id,
                "home_id": home_id,
                "away_id": away_id,
                "home_score": event.home_score,
                "away_score": event.away_score,
            },
        )
