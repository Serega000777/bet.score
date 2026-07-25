from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from bet_score.application.auth import AuthService
from bet_score.application.catalog import CatalogService
from bet_score.config import get_settings
from bet_score.infrastructure.catalog_repository import SqlAlchemyCatalogRepository
from bet_score.infrastructure.database import get_database_session
from bet_score.infrastructure.identity_repository import SqlAlchemyIdentityRepository
from bet_score.infrastructure.telegram_auth import TelegramInitDataVerifier


def get_catalog_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> CatalogService:
    return CatalogService(SqlAlchemyCatalogRepository(session))


CatalogServiceDependency = Annotated[CatalogService, Depends(get_catalog_service)]


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> AuthService:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram-авторизация не настроена",
        )
    return AuthService(
        SqlAlchemyIdentityRepository(session),
        TelegramInitDataVerifier(
            settings.telegram_bot_token,
            max_age=timedelta(seconds=settings.telegram_init_data_ttl_seconds),
        ),
        session_ttl=timedelta(days=settings.session_ttl_days),
    )


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]
