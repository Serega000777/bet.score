import hashlib
import json
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from bet_score.domain.ingestion import ProviderEvent

MAX_PAYLOAD_BYTES = 1_000_000


class IngestionConflictError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class IngestionResult:
    event_id: UUID
    snapshot_created: bool


class EventIngestionRepository(Protocol):
    async def ingest(
        self,
        event: ProviderEvent,
        *,
        payload: dict[str, Any],
        checksum: str,
    ) -> IngestionResult: ...


class EventIngestionService:
    def __init__(self, repository: EventIngestionRepository) -> None:
        self._repository = repository

    async def ingest(
        self,
        event: ProviderEvent,
        *,
        payload: dict[str, Any],
    ) -> IngestionResult:
        serialized_payload = json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        if len(serialized_payload.encode()) > MAX_PAYLOAD_BYTES:
            raise ValueError("Payload поставщика превышает допустимый размер")
        checksum = hashlib.sha256(serialized_payload.encode()).hexdigest()
        return await self._repository.ingest(event, payload=payload, checksum=checksum)
