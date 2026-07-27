from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bet_score.application.live import LiveConnectionRegistry
from bet_score.config import get_settings
from bet_score.infrastructure.database import dispose_engine
from bet_score.infrastructure.observability import HttpMetrics, configure_observability
from bet_score.presentation.api.router import api_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    metrics = HttpMetrics(live_connection_limit=settings.live_max_connections)
    live_connections = LiveConnectionRegistry(
        total_limit=settings.live_max_connections,
        per_event_limit=settings.live_max_connections_per_event,
    )
    application = FastAPI(
        title="bet.score API",
        description="API платформы объяснимой спортивной аналитики",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.api_cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
        expose_headers=["X-Request-ID"],
    )
    application.state.http_metrics = metrics
    application.state.live_connections = live_connections
    configure_observability(application, metrics)
    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
