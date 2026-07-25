from datetime import UTC, datetime

from sqlalchemy import insert, select, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.ext.asyncio import AsyncSession

from bet_score.domain.identity import ExternalIdentity, User
from bet_score.infrastructure.identity_tables import app_user, user_session


class SqlAlchemyIdentityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_user(self, identity: ExternalIdentity) -> User:
        statement = (
            postgresql_insert(app_user)
            .values(
                external_subject=identity.subject,
                display_name=identity.display_name,
                username=identity.username,
                locale=identity.locale,
            )
            .on_conflict_do_update(
                index_elements=[app_user.c.external_subject],
                set_={
                    "display_name": identity.display_name,
                    "username": identity.username,
                    "locale": identity.locale,
                    "updated_at": datetime.now(UTC),
                },
            )
            .returning(
                app_user.c.id,
                app_user.c.display_name,
                app_user.c.username,
                app_user.c.locale,
            )
        )
        row = (await self._session.execute(statement)).one()
        await self._session.commit()
        return User(
            id=row.id, display_name=row.display_name, username=row.username, locale=row.locale
        )

    async def create_session(
        self,
        *,
        user: User,
        token_hash: bytes,
        expires_at: datetime,
    ) -> None:
        await self._session.execute(
            insert(user_session).values(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                revoked=False,
            )
        )
        await self._session.commit()

    async def get_user_by_session(self, token_hash: bytes, now: datetime) -> User | None:
        statement = (
            select(
                app_user.c.id,
                app_user.c.display_name,
                app_user.c.username,
                app_user.c.locale,
            )
            .join(user_session, user_session.c.user_id == app_user.c.id)
            .where(
                user_session.c.token_hash == token_hash,
                user_session.c.expires_at > now,
                user_session.c.revoked.is_(False),
            )
        )
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        return User(
            id=row.id, display_name=row.display_name, username=row.username, locale=row.locale
        )

    async def revoke_session(self, token_hash: bytes) -> None:
        await self._session.execute(
            update(user_session).where(user_session.c.token_hash == token_hash).values(revoked=True)
        )
        await self._session.commit()
