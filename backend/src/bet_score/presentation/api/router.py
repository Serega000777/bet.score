from fastapi import APIRouter

from bet_score.presentation.api.routes.events import router as events_router
from bet_score.presentation.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(events_router)
