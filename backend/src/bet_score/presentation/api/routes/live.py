from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from bet_score.application.catalog import EventNotFoundError
from bet_score.application.live import EventUpdated, stream_live_messages
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

    registry = websocket.app.state.live_connections
    metrics = websocket.app.state.http_metrics
    if not await registry.try_acquire(event_id):
        metrics.reject_live_connection()
        await websocket.close(code=4429, reason="connection_limit_reached")
        return
    metrics.set_live_connections(registry.total)
    try:
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
            async for message in stream_live_messages(
                subscriber,
                event_id,
                heartbeat_seconds=get_settings().live_heartbeat_seconds,
            ):
                payload: dict[str, str | int] = {
                    "type": message.type,
                    "protocol_version": message.protocol_version,
                }
                if isinstance(message, EventUpdated):
                    payload["event_id"] = str(message.event_id)
                await websocket.send_json(payload)
        except WebSocketDisconnect:
            return
        except RedisError:
            await websocket.close(code=1013, reason="stream_unavailable")
    finally:
        await registry.release(event_id)
        metrics.set_live_connections(registry.total)
