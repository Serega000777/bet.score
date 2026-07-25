import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qsl, urlencode
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from bet_score.application.auth import AuthenticationError, AuthService
from bet_score.domain.identity import ExternalIdentity, User
from bet_score.infrastructure.telegram_auth import TelegramInitDataVerifier
from bet_score.main import create_app
from bet_score.presentation.api.dependencies import get_auth_service

BOT_TOKEN = "123456:test-token"
USER = User(
    id=UUID("50000000-0000-0000-0000-000000000001"),
    display_name="Иван Петров",
    username="ivan",
    locale="ru",
)


def signed_init_data(*, auth_date: datetime, first_name: str = "Иван") -> str:
    parameters = {
        "auth_date": str(int(auth_date.timestamp())),
        "query_id": "AAEAAAE",
        "user": json.dumps(
            {
                "id": 42,
                "first_name": first_name,
                "last_name": "Петров",
                "username": "ivan",
                "language_code": "ru",
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }
    check_string = "\n".join(f"{key}={value}" for key, value in sorted(parameters.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    parameters["hash"] = hmac.new(
        secret,
        check_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    return urlencode(parameters)


def test_telegram_verifier_accepts_valid_fresh_data() -> None:
    verifier = TelegramInitDataVerifier(BOT_TOKEN, max_age=timedelta(minutes=10))

    identity = verifier.verify(signed_init_data(auth_date=datetime.now(UTC)))

    assert identity.subject == "telegram:42"
    assert identity.display_name == "Иван Петров"


def test_telegram_verifier_rejects_tampering() -> None:
    verifier = TelegramInitDataVerifier(BOT_TOKEN, max_age=timedelta(minutes=10))
    parameters = dict(parse_qsl(signed_init_data(auth_date=datetime.now(UTC))))
    user = json.loads(parameters["user"])
    user["first_name"] = "Пётр"
    parameters["user"] = json.dumps(user, ensure_ascii=False, separators=(",", ":"))

    with pytest.raises(AuthenticationError, match="подпись"):
        verifier.verify(urlencode(parameters))


def test_telegram_verifier_rejects_expired_data() -> None:
    verifier = TelegramInitDataVerifier(BOT_TOKEN, max_age=timedelta(minutes=10))

    with pytest.raises(AuthenticationError, match="устарели"):
        verifier.verify(signed_init_data(auth_date=datetime.now(UTC) - timedelta(hours=1)))


class FakeVerifier:
    def verify(self, init_data: str) -> ExternalIdentity:
        assert init_data == "signed"
        return ExternalIdentity(
            subject="telegram:42",
            display_name=USER.display_name,
            username=USER.username,
            locale=USER.locale,
        )


class FakeIdentityRepository:
    def __init__(self) -> None:
        self.token_hash: bytes | None = None
        self.revoked_hash: bytes | None = None

    async def upsert_user(self, identity: ExternalIdentity) -> User:
        assert identity.subject == "telegram:42"
        return USER

    async def create_session(
        self,
        *,
        user: User,
        token_hash: bytes,
        expires_at: datetime,
    ) -> None:
        assert user == USER
        assert expires_at > datetime.now(UTC)
        self.token_hash = token_hash

    async def get_user_by_session(self, token_hash: bytes, now: datetime) -> User | None:
        return USER if token_hash == self.token_hash else None

    async def revoke_session(self, token_hash: bytes) -> None:
        self.revoked_hash = token_hash


@pytest.mark.asyncio
async def test_auth_service_stores_only_token_hash_and_revokes_it() -> None:
    repository = FakeIdentityRepository()
    service = AuthService(repository, FakeVerifier(), session_ttl=timedelta(days=30))

    session = await service.authenticate_telegram("signed")

    assert repository.token_hash == service.hash_token(session.token)
    assert session.token.encode() not in repository.token_hash
    assert await service.get_user(session.token) == USER

    await service.sign_out(session.token)
    assert repository.revoked_hash == repository.token_hash


@pytest.mark.asyncio
async def test_telegram_auth_sets_protected_session_cookie() -> None:
    repository = FakeIdentityRepository()
    service = AuthService(repository, FakeVerifier(), session_ttl=timedelta(days=30))
    application = create_app()
    application.dependency_overrides[get_auth_service] = lambda: service

    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/auth/telegram",
            json={"init_data": "signed"},
        )

    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Secure" not in cookie
