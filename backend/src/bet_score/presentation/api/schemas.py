from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from bet_score.domain.catalog import (
    CompetitionSummary,
    Participant,
    SportingEvent,
    SportSummary,
)


class ParticipantResponse(BaseModel):
    id: UUID
    name: str
    short_name: str
    role: Literal["home", "away"]
    score: int | None


class EventResponse(BaseModel):
    id: UUID
    sport_code: str
    sport: str
    competition_id: UUID
    competition: str
    country_code: str | None
    starts_at: datetime
    status: Literal["scheduled", "live", "finished", "postponed", "cancelled"]
    home: ParticipantResponse
    away: ParticipantResponse

    @classmethod
    def from_domain(cls, event: SportingEvent) -> "EventResponse":
        def participant(item: Participant) -> ParticipantResponse:
            return ParticipantResponse(
                id=item.id,
                name=item.name,
                short_name=item.short_name,
                role=item.role.value,
                score=item.score,
            )

        return cls(
            id=event.id,
            sport_code=event.sport_code,
            sport=event.sport_name,
            competition_id=event.competition_id,
            competition=event.competition_name,
            country_code=event.country_code,
            starts_at=event.starts_at,
            status=event.status.value,
            home=participant(event.home),
            away=participant(event.away),
        )


class EventListResponse(BaseModel):
    items: list[EventResponse]
    count: int


class SportResponse(BaseModel):
    code: str
    name: str
    event_count: int

    @classmethod
    def from_domain(cls, item: SportSummary) -> "SportResponse":
        return cls(code=item.code, name=item.name, event_count=item.event_count)


class SportListResponse(BaseModel):
    items: list[SportResponse]
    count: int


class CompetitionResponse(BaseModel):
    id: UUID
    sport_code: str
    name: str
    country_code: str | None
    event_count: int

    @classmethod
    def from_domain(cls, item: CompetitionSummary) -> "CompetitionResponse":
        return cls(
            id=item.id,
            sport_code=item.sport_code,
            name=item.name,
            country_code=item.country_code,
            event_count=item.event_count,
        )


class CompetitionListResponse(BaseModel):
    items: list[CompetitionResponse]
    count: int


class EventProvenanceResponse(BaseModel):
    provider_key: str
    version: str
    observed_at: datetime
    ingested_at: datetime
    checksum: str


class EventProvenanceListResponse(BaseModel):
    items: list[EventProvenanceResponse]
    count: int


class ErrorResponse(BaseModel):
    code: str
    message: str


class TelegramAuthRequest(BaseModel):
    init_data: str


class UserResponse(BaseModel):
    id: UUID
    display_name: str
    username: str | None
    locale: str
