import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from bet_score.domain.identity import ExternalIdentity, User


class AuthenticationError(Exception):
    pass


class TelegramDataVerifier(Protocol):
    def verify(self, init_data: str) -> ExternalIdentity: ...


class IdentityRepository(Protocol):
    async def upsert_user(self, identity: ExternalIdentity) -> User: ...

    async def create_session(
        self,
        *,
        user: User,
        token_hash: bytes,
        expires_at: datetime,
    ) -> None: ...

    async def get_user_by_session(self, token_hash: bytes, now: datetime) -> User | None: ...

    async def revoke_session(self, token_hash: bytes) -> None: ...


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    user: User
    token: str
    expires_at: datetime


class AuthService:
    def __init__(
        self,
        repository: IdentityRepository,
        verifier: TelegramDataVerifier,
        *,
        session_ttl: timedelta,
    ) -> None:
        self._repository = repository
        self._verifier = verifier
        self._session_ttl = session_ttl

    async def authenticate_telegram(self, init_data: str) -> AuthenticatedSession:
        identity = self._verifier.verify(init_data)
        user = await self._repository.upsert_user(identity)
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + self._session_ttl
        await self._repository.create_session(
            user=user,
            token_hash=self.hash_token(token),
            expires_at=expires_at,
        )
        return AuthenticatedSession(user=user, token=token, expires_at=expires_at)

    async def get_user(self, token: str | None) -> User | None:
        if not token:
            return None
        return await self._repository.get_user_by_session(
            self.hash_token(token),
            datetime.now(UTC),
        )

    async def sign_out(self, token: str | None) -> None:
        if token:
            await self._repository.revoke_session(self.hash_token(token))

    @staticmethod
    def hash_token(token: str) -> bytes:
        return hashlib.sha256(token.encode()).digest()
