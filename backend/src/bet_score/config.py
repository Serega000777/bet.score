from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://bet_score:bet_score@localhost:5432/bet_score"
    redis_url: str = "redis://localhost:6379/0"
    readiness_timeout_seconds: float = Field(default=2.0, gt=0, le=30)
    live_heartbeat_seconds: float = Field(default=20.0, ge=5, le=60)
    live_max_connections: int = Field(default=1000, ge=1, le=100_000)
    live_max_connections_per_event: int = Field(default=200, ge=1, le=10_000)
    outbox_batch_size: int = Field(default=100, ge=1, le=1000)
    outbox_lease_seconds: float = Field(default=30, ge=5, le=300)
    outbox_poll_seconds: float = Field(default=1, ge=0.1, le=30)
    api_cors_origins: Annotated[tuple[str, ...], NoDecode] = (
        "http://localhost:3000",
        "http://localhost:3001",
    )
    telegram_bot_token: str | None = None
    telegram_init_data_ttl_seconds: int = 600
    session_cookie_name: str = "bet_score_session"
    session_ttl_days: int = 30

    @property
    def secure_cookies(self) -> bool:
        return self.app_env in {"staging", "production"}

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("api_cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(origin.strip() for origin in value.split(",") if origin.strip())
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
