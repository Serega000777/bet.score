from typing import Literal

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from bet_score.config import get_settings

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=get_settings().app_version)


@router.get("/metrics", include_in_schema=False)
async def metrics(request: Request) -> Response:
    return Response(
        content=request.app.state.http_metrics.render(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
