from datetime import datetime

from fastapi import APIRouter, Query

from bet_score.presentation.api.dependencies import CatalogServiceDependency
from bet_score.presentation.api.schemas import (
    CompetitionListResponse,
    CompetitionResponse,
    SportListResponse,
    SportResponse,
)

router = APIRouter(tags=["catalog"])


@router.get("/sports", response_model=SportListResponse)
async def list_sports(
    service: CatalogServiceDependency,
    starts_from: datetime | None = None,
) -> SportListResponse:
    items = [
        SportResponse.from_domain(item)
        for item in await service.list_sports(starts_from=starts_from)
    ]
    return SportListResponse(items=items, count=len(items))


@router.get("/competitions", response_model=CompetitionListResponse)
async def list_competitions(
    service: CatalogServiceDependency,
    starts_from: datetime | None = None,
    sport_code: str | None = Query(default=None, min_length=1, max_length=50),
) -> CompetitionListResponse:
    items = [
        CompetitionResponse.from_domain(item)
        for item in await service.list_competitions(
            starts_from=starts_from,
            sport_code=sport_code,
        )
    ]
    return CompetitionListResponse(items=items, count=len(items))
