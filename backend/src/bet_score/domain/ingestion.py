from dataclasses import dataclass
from datetime import datetime
from re import fullmatch

from bet_score.domain.catalog import EventStatus


@dataclass(frozen=True, slots=True)
class ProviderTeam:
    external_id: str
    name: str
    short_name: str
    country_code: str | None = None

    def __post_init__(self) -> None:
        _validate_text(self.external_id, "ID команды", 255)
        _validate_text(self.name, "Название команды", 255)
        _validate_text(self.short_name, "Короткое название команды", 32)
        _validate_country(self.country_code)


@dataclass(frozen=True, slots=True)
class ProviderCompetition:
    external_id: str
    name: str
    country_code: str | None = None

    def __post_init__(self) -> None:
        _validate_text(self.external_id, "ID соревнования", 255)
        _validate_text(self.name, "Название соревнования", 255)
        _validate_country(self.country_code)


@dataclass(frozen=True, slots=True)
class ProviderEvent:
    provider_key: str
    external_id: str
    version: str
    observed_at: datetime
    sport_code: str
    sport_name: str
    competition: ProviderCompetition
    starts_at: datetime
    status: EventStatus
    home: ProviderTeam
    away: ProviderTeam
    home_score: int | None = None
    away_score: int | None = None

    def __post_init__(self) -> None:
        if fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", self.provider_key) is None:
            raise ValueError("Ключ поставщика имеет недопустимый формат")
        _validate_text(self.external_id, "ID события", 255)
        _validate_text(self.version, "Версия события", 255)
        _validate_text(self.sport_code, "Код вида спорта", 64)
        _validate_text(self.sport_name, "Название вида спорта", 255)
        if self.observed_at.utcoffset() is None or self.starts_at.utcoffset() is None:
            raise ValueError("Время ingestion должно содержать часовой пояс")
        if self.home.external_id == self.away.external_id:
            raise ValueError("Хозяева и гости должны быть разными командами")
        scores = (self.home_score, self.away_score)
        if any(score is not None and score < 0 for score in scores):
            raise ValueError("Счёт матча не может быть отрицательным")


def _validate_text(value: str, label: str, max_length: int) -> None:
    if not value.strip() or len(value) > max_length:
        raise ValueError(f"{label}: недопустимая длина")


def _validate_country(value: str | None) -> None:
    if value is not None and fullmatch(r"[A-Z]{2}", value) is None:
        raise ValueError("Код страны должен соответствовать ISO 3166-1 alpha-2")
