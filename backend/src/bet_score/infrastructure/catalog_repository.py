from collections import defaultdict
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from bet_score.application.catalog import EventQuery
from bet_score.domain.catalog import EventStatus, Participant, ParticipantRole, SportingEvent
from bet_score.infrastructure.catalog_tables import (
    competition,
    event_participant,
    sport,
    sporting_event,
    team,
)


class SqlAlchemyCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_events(self, query: EventQuery) -> tuple[SportingEvent, ...]:
        statement = self._base_statement().where(sporting_event.c.starts_at >= query.starts_from)
        statement = statement.order_by(sporting_event.c.starts_at).limit(query.limit * 2)
        rows = (await self._session.execute(statement)).mappings().all()
        events = self._map_events(rows)
        return tuple(events[: query.limit])

    async def get_event(self, event_id: UUID) -> SportingEvent | None:
        statement = self._base_statement().where(sporting_event.c.id == event_id)
        rows = (await self._session.execute(statement)).mappings().all()
        events = self._map_events(rows)
        return events[0] if events else None

    @staticmethod
    def _base_statement() -> Select[Any]:
        return (
            select(
                sporting_event.c.id.label("event_id"),
                sporting_event.c.starts_at,
                sporting_event.c.status,
                sport.c.code.label("sport_code"),
                sport.c.name.label("sport_name"),
                competition.c.id.label("competition_id"),
                competition.c.name.label("competition_name"),
                competition.c.country_code,
                team.c.id.label("team_id"),
                team.c.name.label("team_name"),
                team.c.short_name,
                event_participant.c.role,
                event_participant.c.score,
            )
            .join(competition, competition.c.id == sporting_event.c.competition_id)
            .join(sport, sport.c.id == competition.c.sport_id)
            .join(event_participant, event_participant.c.event_id == sporting_event.c.id)
            .join(team, team.c.id == event_participant.c.team_id)
        )

    @staticmethod
    def _map_events(rows: Sequence[RowMapping]) -> list[SportingEvent]:
        grouped: dict[UUID, list[RowMapping]] = defaultdict(list)
        for row in rows:
            grouped[row["event_id"]].append(row)

        result: list[SportingEvent] = []
        for event_rows in grouped.values():
            first = event_rows[0]
            participants = tuple(
                Participant(
                    id=row["team_id"],
                    name=row["team_name"],
                    short_name=row["short_name"],
                    role=ParticipantRole(row["role"]),
                    score=row["score"],
                )
                for row in event_rows
            )
            result.append(
                SportingEvent(
                    id=first["event_id"],
                    sport_code=first["sport_code"],
                    sport_name=first["sport_name"],
                    competition_id=first["competition_id"],
                    competition_name=first["competition_name"],
                    country_code=first["country_code"],
                    starts_at=first["starts_at"],
                    status=EventStatus(first["status"]),
                    participants=participants,
                )
            )
        result.sort(key=lambda event: event.starts_at)
        return result
