from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from bet_score.application.catalog import EventNotFoundError
from bet_score.presentation.api.dependencies import CatalogServiceDependency
from bet_score.presentation.api.schemas import (
    ErrorResponse,
    EventListResponse,
    EventProvenanceListResponse,
    EventProvenanceResponse,
    EventResponse,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListResponse)
async def list_events(
    service: CatalogServiceDependency,
    starts_from: datetime | None = None,
    limit: int = Query(default=20, ge=1, le=100),
) -> EventListResponse:
    events = await service.list_upcoming_events(starts_from=starts_from, limit=limit)
    items = [EventResponse.from_domain(event) for event in events]
    return EventListResponse(items=items, count=len(items))


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_event(
    event_id: UUID,
    service: CatalogServiceDependency,
) -> EventResponse | JSONResponse:
    try:
        event = await service.get_event(event_id)
    except EventNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"code": "event_not_found", "message": str(error)},
        )
    return EventResponse.from_domain(event)


@router.get(
    "/{event_id}/provenance",
    response_model=EventProvenanceListResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_event_provenance(
    event_id: UUID,
    service: CatalogServiceDependency,
) -> EventProvenanceListResponse | JSONResponse:
    try:
        sources = await service.list_event_provenance(event_id)
    except EventNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"code": "event_not_found", "message": str(error)},
        )
    items = [
        EventProvenanceResponse(
            provider_key=source.provider_key,
            version=source.version,
            observed_at=source.observed_at,
            ingested_at=source.ingested_at,
            checksum=source.checksum,
        )
        for source in sources
    ]
    return EventProvenanceListResponse(items=items, count=len(items))
