from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from bet_score.application.auth import AuthService
from bet_score.application.catalog import CatalogService
from bet_score.application.live import EventUpdateSubscriber
from bet_score.application.outbox import OutboxStatsReader
from bet_score.application.readiness import ReadinessService
from bet_score.application.saved_events import SavedEventsService
from bet_score.config import get_settings
from bet_score.domain.identity import User
from bet_score.infrastructure.catalog_repository import SqlAlchemyCatalogRepository
from bet_score.infrastructure.database import get_database_session
from bet_score.infrastructure.identity_repository import SqlAlchemyIdentityRepository
from bet_score.infrastructure.live import RedisEventUpdateBroker
from bet_score.infrastructure.outbox_stats import SqlAlchemyOutboxStatsReader
from bet_score.infrastructure.readiness import probe_database, probe_redis
from bet_score.infrastructure.saved_event_repository import SqlAlchemySavedEventRepository
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


async def get_current_user(
    request: Request,
    service: AuthServiceDependency,
) -> User:
    user = await service.get_user(request.cookies.get(get_settings().session_cookie_name))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
        )
    return user


CurrentUserDependency = Annotated[User, Depends(get_current_user)]


def get_saved_events_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> SavedEventsService:
    return SavedEventsService(
        SqlAlchemySavedEventRepository(session),
        SqlAlchemyCatalogRepository(session),
    )


SavedEventsServiceDependency = Annotated[
    SavedEventsService,
    Depends(get_saved_events_service),
]


def get_readiness_service() -> ReadinessService:
    settings = get_settings()
    return ReadinessService(
        {"postgres": probe_database, "redis": probe_redis},
        timeout_seconds=settings.readiness_timeout_seconds,
    )


ReadinessServiceDependency = Annotated[ReadinessService, Depends(get_readiness_service)]


def get_event_update_subscriber() -> EventUpdateSubscriber:
    return RedisEventUpdateBroker(get_settings().redis_url)


EventUpdateSubscriberDependency = Annotated[
    EventUpdateSubscriber,
    Depends(get_event_update_subscriber),
]


def get_outbox_stats_reader(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> OutboxStatsReader:
    return SqlAlchemyOutboxStatsReader(session)


OutboxStatsReaderDependency = Annotated[OutboxStatsReader, Depends(get_outbox_stats_reader)]
