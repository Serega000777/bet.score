import asyncio
import logging

from bet_score.application.outbox import OutboxDispatcher
from bet_score.config import get_settings
from bet_score.infrastructure.database import dispose_engine, get_engine
from bet_score.infrastructure.live import RedisEventUpdateBroker
from bet_score.infrastructure.outbox_repository import SqlAlchemyOutboxRepository

logger = logging.getLogger("bet_score.outbox")


async def run() -> None:
    settings = get_settings()
    dispatcher = OutboxDispatcher(
        SqlAlchemyOutboxRepository(get_engine()),
        RedisEventUpdateBroker(settings.redis_url),
    )
    try:
        while True:
            try:
                delivered = await dispatcher.run_once(
                    batch_size=settings.outbox_batch_size,
                    lease_seconds=settings.outbox_lease_seconds,
                )
            except Exception:
                logger.warning("outbox_dispatch_failed")
                delivered = 0
            if delivered == 0:
                await asyncio.sleep(settings.outbox_poll_seconds)
    finally:
        await dispose_engine()


def main() -> None:
    asyncio.run(run())
