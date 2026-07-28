from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class EventStatus(StrEnum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class ParticipantRole(StrEnum):
    HOME = "home"
    AWAY = "away"


@dataclass(frozen=True, slots=True)
class Participant:
    id: UUID
    name: str
    short_name: str
    role: ParticipantRole
    score: int | None = None


@dataclass(frozen=True, slots=True)
class SportingEvent:
    id: UUID
    sport_code: str
    sport_name: str
    competition_id: UUID
    competition_name: str
    country_code: str | None
    starts_at: datetime
    status: EventStatus
    participants: tuple[Participant, ...]

    def __post_init__(self) -> None:
        roles = {participant.role for participant in self.participants}
        required_roles = {ParticipantRole.HOME, ParticipantRole.AWAY}
        if roles != required_roles or len(self.participants) != 2:
            raise ValueError("Матч должен содержать ровно одного хозяина и одного гостя")

    @property
    def home(self) -> Participant:
        return next(item for item in self.participants if item.role is ParticipantRole.HOME)

    @property
    def away(self) -> Participant:
        return next(item for item in self.participants if item.role is ParticipantRole.AWAY)


@dataclass(frozen=True, slots=True)
class EventProvenance:
    provider_key: str
    version: str
    observed_at: datetime
    ingested_at: datetime
    checksum: str


@dataclass(frozen=True, slots=True)
class SportSummary:
    code: str
    name: str
    event_count: int


@dataclass(frozen=True, slots=True)
class CompetitionSummary:
    id: UUID
    sport_code: str
    name: str
    country_code: str | None
    event_count: int
