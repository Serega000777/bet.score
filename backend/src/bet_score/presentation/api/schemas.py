from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from bet_score.domain.catalog import Participant, SportingEvent


class ParticipantResponse(BaseModel):
    id: UUID
    name: str
    short_name: str
    role: Literal["home", "away"]
    score: int | None


class EventResponse(BaseModel):
    id: UUID
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
