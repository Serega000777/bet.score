from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from bet_score.application.catalog import EventNotFoundError
from bet_score.config import get_settings
from bet_score.presentation.api.dependencies import (
    CatalogServiceDependency,
    EventUpdateSubscriberDependency,
)

router = APIRouter(prefix="/live", tags=["live"])


@router.websocket("/events/{event_id}")
async def event_updates(
    websocket: WebSocket,
    event_id: UUID,
    catalog: CatalogServiceDependency,
    subscriber: EventUpdateSubscriberDependency,
) -> None:
    origin = websocket.headers.get("origin")
    if origin not in get_settings().api_cors_origins:
        await websocket.close(code=4403, reason="origin_not_allowed")
        return
    try:
        await catalog.get_event(event_id)
    except EventNotFoundError:
        await websocket.close(code=4404, reason="event_not_found")
        return
    except SQLAlchemyError:
        await websocket.close(code=1013, reason="service_unavailable")
        return

    await websocket.accept()
    try:
        async for update in subscriber.subscribe(event_id):
            await websocket.send_json(
                {
                    "type": update.type,
                    "protocol_version": update.protocol_version,
                    "event_id": str(update.event_id),
                }
            )
    except WebSocketDisconnect:
        return
    except RedisError:
        await websocket.close(code=1013, reason="stream_unavailable")
