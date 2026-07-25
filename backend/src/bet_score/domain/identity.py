from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ExternalIdentity:
    subject: str
    display_name: str
    username: str | None
    locale: str


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    display_name: str
    username: str | None
    locale: str
