import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qsl

from bet_score.application.auth import AuthenticationError
from bet_score.domain.identity import ExternalIdentity


class TelegramInitDataVerifier:
    def __init__(self, bot_token: str, *, max_age: timedelta) -> None:
        self._bot_token = bot_token
        self._max_age = max_age

    def verify(self, init_data: str) -> ExternalIdentity:
        try:
            parameters = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
        except ValueError as error:
            raise AuthenticationError("Некорректные данные Telegram") from error
        received_hash = parameters.pop("hash", None)
        if not received_hash:
            raise AuthenticationError("Telegram не передал подпись")

        data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parameters.items()))
        secret = hmac.new(
            b"WebAppData",
            self._bot_token.encode(),
            hashlib.sha256,
        ).digest()
        expected_hash = hmac.new(
            secret,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(received_hash, expected_hash):
            raise AuthenticationError("Некорректная подпись Telegram")

        auth_date = self._parse_auth_date(parameters.get("auth_date"))
        now = datetime.now(UTC)
        if auth_date > now + timedelta(seconds=30) or now - auth_date > self._max_age:
            raise AuthenticationError("Данные Telegram устарели")

        return self._parse_user(parameters.get("user"))

    @staticmethod
    def _parse_auth_date(value: str | None) -> datetime:
        try:
            return datetime.fromtimestamp(int(value or ""), tz=UTC)
        except (ValueError, OSError) as error:
            raise AuthenticationError("Некорректная дата Telegram") from error

    @staticmethod
    def _parse_user(value: str | None) -> ExternalIdentity:
        try:
            payload = json.loads(value or "")
            if not isinstance(payload, dict):
                raise TypeError
            telegram_id = int(payload["id"])
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            raise AuthenticationError("Telegram не передал пользователя") from error

        first_name = str(payload.get("first_name", "")).strip()
        last_name = str(payload.get("last_name", "")).strip()
        display_name = " ".join(part for part in (first_name, last_name) if part)
        if not display_name:
            raise AuthenticationError("Telegram не передал имя пользователя")

        username = payload.get("username")
        language_code = str(payload.get("language_code") or "ru")
        return ExternalIdentity(
            subject=f"telegram:{telegram_id}",
            display_name=display_name,
            username=str(username) if username else None,
            locale=language_code[:10],
        )
