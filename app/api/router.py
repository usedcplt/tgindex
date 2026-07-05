"""Main API router."""

from fastapi import APIRouter

from app.config import settings

from .endpoints import (
    chats_router,
    search_router,
    sources_router,
    statistics_router,
    system_router,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(search_router)
api_router.include_router(chats_router)
api_router.include_router(statistics_router)
api_router.include_router(sources_router)
api_router.include_router(system_router)
