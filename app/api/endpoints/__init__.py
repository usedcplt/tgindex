"""API endpoints."""

from .chats import router as chats_router
from .search import router as search_router
from .sources import router as sources_router
from .statistics import router as statistics_router
from .system import router as system_router

__all__ = [
    "chats_router",
    "search_router",
    "sources_router",
    "statistics_router",
    "system_router",
]
