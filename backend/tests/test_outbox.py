from uuid import UUID

import pytest

from bet_score.application.live import EventUpdated
from bet_score.application.outbox import OutboxDispatcher, OutboxMessage

EVENT_ID = UUID("80000000-0000-0000-0000-000000000001")


class FakeOutboxRepository:
    def __init__(self, messages: list[OutboxMessage]) -> None:
        self.messages = messages
        self.delivered: list[int] = []
        self.failed: list[tuple[int, float]] = []

    async def claim(self, *, batch_size: int, lease_seconds: float) -> list[OutboxMessage]:
        assert batch_size == 10
        assert lease_seconds == 30
        return self.messages

    async def mark_delivered(self, message_id: int) -> None:
        self.delivered.append(message_id)

    async def mark_failed(self, message_id: int, *, retry_seconds: float) -> None:
        self.failed.append((message_id, retry_seconds))


class FakePublisher:
    def __init__(self, *, fail_event_id: UUID | None = None) -> None:
        self.fail_event_id = fail_event_id
        self.updates: list[EventUpdated] = []

    async def publish(self, update: EventUpdated) -> None:
        if update.event_id == self.fail_event_id:
            raise OSError("Redis is unavailable")
        self.updates.append(update)


@pytest.mark.asyncio
async def test_dispatcher_marks_published_messages_delivered() -> None:
    repository = FakeOutboxRepository([OutboxMessage(1, EVENT_ID, attempts=1)])
    publisher = FakePublisher()
    dispatcher = OutboxDispatcher(repository, publisher)

    delivered = await dispatcher.run_once(batch_size=10, lease_seconds=30)

    assert delivered == 1
    assert publisher.updates == [EventUpdated(event_id=EVENT_ID)]
    assert repository.delivered == [1]
    assert repository.failed == []


@pytest.mark.asyncio
async def test_dispatcher_isolates_failure_and_schedules_bounded_retry() -> None:
    failed_event_id = UUID("80000000-0000-0000-0000-000000000002")
    repository = FakeOutboxRepository(
        [
            OutboxMessage(1, failed_event_id, attempts=20),
            OutboxMessage(2, EVENT_ID, attempts=1),
        ]
    )
    publisher = FakePublisher(fail_event_id=failed_event_id)
    dispatcher = OutboxDispatcher(repository, publisher)

    delivered = await dispatcher.run_once(batch_size=10, lease_seconds=30)

    assert delivered == 1
    assert repository.failed == [(1, 300)]
    assert repository.delivered == [2]
