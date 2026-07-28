from uuid import UUID

from fastapi import APIRouter, Query, Response, status
from fastapi.responses import JSONResponse

from bet_score.application.saved_events import SavedEventNotFoundError
from bet_score.presentation.api.dependencies import (
    CurrentUserDependency,
    SavedEventsServiceDependency,
)
from bet_score.presentation.api.schemas import ErrorResponse, EventListResponse, EventResponse

router = APIRouter(prefix="/saved-events", tags=["saved-events"])


@router.get("", response_model=EventListResponse)
async def list_saved_events(
    user: CurrentUserDependency,
    service: SavedEventsServiceDependency,
    limit: int = Query(default=50, ge=1, le=100),
) -> EventListResponse:
    events = await service.list_events(user.id, limit=limit)
    items = [EventResponse.from_domain(event) for event in events]
    return EventListResponse(items=items, count=len(items))


@router.put(
    "/{event_id}",
    response_model=None,
    responses={
        204: {"description": "Матч сохранён"},
        404: {"model": ErrorResponse},
    },
)
async def save_event(
    event_id: UUID,
    user: CurrentUserDependency,
    service: SavedEventsServiceDependency,
) -> Response:
    try:
        await service.save(user.id, event_id)
    except SavedEventNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"code": "event_not_found", "message": "Матч не найден"},
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_saved_event(
    event_id: UUID,
    user: CurrentUserDependency,
    service: SavedEventsServiceDependency,
) -> None:
    await service.remove(user.id, event_id)
