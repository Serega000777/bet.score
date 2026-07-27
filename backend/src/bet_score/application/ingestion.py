import hashlib
import json
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from bet_score.application.live import EventUpdated, EventUpdatePublisher
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
    def __init__(
        self,
        repository: EventIngestionRepository,
        publisher: EventUpdatePublisher | None = None,
    ) -> None:
        self._repository = repository
        self._publisher = publisher

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
        result = await self._repository.ingest(event, payload=payload, checksum=checksum)
        if result.snapshot_created and self._publisher is not None:
            await self._publisher.publish(EventUpdated(event_id=result.event_id))
        return result
