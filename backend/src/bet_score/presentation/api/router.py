from fastapi import APIRouter

from bet_score.presentation.api.routes.auth import router as auth_router
from bet_score.presentation.api.routes.catalog import router as catalog_router
from bet_score.presentation.api.routes.events import router as events_router
from bet_score.presentation.api.routes.health import router as health_router
from bet_score.presentation.api.routes.live import router as live_router
from bet_score.presentation.api.routes.saved_events import router as saved_events_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(catalog_router)
api_router.include_router(events_router)
api_router.include_router(live_router)
api_router.include_router(saved_events_router)
