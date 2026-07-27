from typing import cast
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from bet_score.application.outbox import OutboxMessage


class SqlAlchemyOutboxRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def claim(self, *, batch_size: int, lease_seconds: float) -> list[OutboxMessage]:
        async with self._engine.begin() as connection:
            rows = (
                await connection.execute(
                    text(
                        """
                        WITH candidates AS (
                          SELECT id
                          FROM event_outbox
                          WHERE delivered_at IS NULL
                            AND available_at <= now()
                            AND (locked_until IS NULL OR locked_until < now())
                          ORDER BY id
                          FOR UPDATE SKIP LOCKED
                          LIMIT :batch_size
                        )
                        UPDATE event_outbox AS outbox
                        SET attempts = attempts + 1,
                            locked_until = now() + make_interval(secs => :lease_seconds)
                        FROM candidates
                        WHERE outbox.id = candidates.id
                        RETURNING outbox.id, outbox.event_id, outbox.attempts
                        """
                    ),
                    {
                        "batch_size": batch_size,
                        "lease_seconds": lease_seconds,
                    },
                )
            ).all()
        return [
            OutboxMessage(
                id=cast(int, row.id),
                event_id=cast(UUID, row.event_id),
                attempts=cast(int, row.attempts),
            )
            for row in rows
        ]

    async def mark_delivered(self, message_id: int) -> None:
        async with self._engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    UPDATE event_outbox
                    SET delivered_at = now(), locked_until = NULL, last_error_code = NULL
                    WHERE id = :message_id AND delivered_at IS NULL
                    """
                ),
                {"message_id": message_id},
            )

    async def mark_failed(self, message_id: int, *, retry_seconds: float) -> None:
        async with self._engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    UPDATE event_outbox
                    SET available_at = now() + make_interval(secs => :retry_seconds),
                        locked_until = NULL,
                        last_error_code = 'publish_failed'
                    WHERE id = :message_id AND delivered_at IS NULL
                    """
                ),
                {
                    "message_id": message_id,
                    "retry_seconds": retry_seconds,
                },
            )
