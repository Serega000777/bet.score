from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from bet_score.config import get_settings
from bet_score.presentation.api.dependencies import (
    OutboxStatsReaderDependency,
    ReadinessServiceDependency,
)

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "unavailable"]
    checks: dict[str, Literal["ok", "unavailable"]]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=get_settings().app_version)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessResponse}},
)
async def readiness(
    service: ReadinessServiceDependency,
    response: Response,
) -> ReadinessResponse:
    result = await service.check()
    response.headers["Cache-Control"] = "no-store"
    if not result.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ready" if result.ready else "unavailable",
        checks={
            name: "ok" if available else "unavailable" for name, available in result.checks.items()
        },
    )


@router.get("/metrics", include_in_schema=False)
async def metrics(
    request: Request,
    outbox_reader: OutboxStatsReaderDependency,
) -> Response:
    try:
        outbox = await outbox_reader.get_stats()
    except SQLAlchemyError:
        outbox = None
    return Response(
        content=request.app.state.http_metrics.render(outbox),
        media_type="text/plain; version=0.0.4; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )
