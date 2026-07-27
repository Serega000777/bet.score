from typing import cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from bet_score.application.outbox import OutboxStats


class SqlAlchemyOutboxStatsReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_stats(self) -> OutboxStats:
        row = (
            await self._session.execute(
                text(
                    """
                    SELECT
                      pending.count AS pending,
                      pending.oldest_pending_seconds,
                      stats.delivered,
                      stats.retries
                    FROM outbox_delivery_stats AS stats
                    CROSS JOIN LATERAL (
                      SELECT
                        count(*) AS count,
                        COALESCE(
                          EXTRACT(EPOCH FROM (now() - min(created_at))),
                          0
                        ) AS oldest_pending_seconds
                      FROM event_outbox
                      WHERE delivered_at IS NULL
                    ) AS pending
                    WHERE stats.singleton
                    """
                )
            )
        ).one()
        return OutboxStats(
            pending=cast(int, row.pending),
            oldest_pending_seconds=float(row.oldest_pending_seconds),
            delivered=cast(int, row.delivered),
            retries=cast(int, row.retries),
        )
