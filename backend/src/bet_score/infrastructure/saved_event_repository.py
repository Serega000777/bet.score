from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from bet_score.infrastructure.saved_event_tables import saved_event


class SqlAlchemySavedEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_event_ids(self, user_id: UUID, limit: int) -> tuple[UUID, ...]:
        result = await self._session.scalars(
            select(saved_event.c.event_id)
            .where(saved_event.c.user_id == user_id)
            .order_by(saved_event.c.created_at.desc())
            .limit(limit)
        )
        return tuple(result)

    async def add(self, user_id: UUID, event_id: UUID) -> None:
        await self._session.execute(
            insert(saved_event).values(user_id=user_id, event_id=event_id).on_conflict_do_nothing()
        )
        await self._session.commit()

    async def remove(self, user_id: UUID, event_id: UUID) -> None:
        await self._session.execute(
            delete(saved_event).where(
                saved_event.c.user_id == user_id,
                saved_event.c.event_id == event_id,
            )
        )
        await self._session.commit()
