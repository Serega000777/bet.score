from redis.asyncio import Redis
from sqlalchemy import text

from bet_score.config import get_settings
from bet_score.infrastructure.database import get_engine


async def probe_database() -> None:
    async with get_engine().connect() as connection:
        await connection.execute(text("SELECT 1"))


async def probe_redis() -> None:
    client = Redis.from_url(get_settings().redis_url)
    try:
        await client.ping()
    finally:
        await client.aclose()
