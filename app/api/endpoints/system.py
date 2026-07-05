"""System API endpoint."""

import time
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.session import get_session
from app.repositories.queue_repository import QueueRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.source_repository import SourceRepository

router = APIRouter(prefix="/system", tags=["system"])

# In-memory activity log
_activity_log: list[dict] = []
_max_log_size = 100


def add_activity(job: str, status: str, details: dict | None = None) -> None:
    """Add activity to log."""
    entry = {
        "time": datetime.utcnow().isoformat(),
        "job": job,
        "status": status,
        "details": details or {},
    }
    _activity_log.append(entry)
    if len(_activity_log) > _max_log_size:
        _activity_log.pop(0)


@router.get("/health")
async def health_check(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Health check endpoint."""
    try:
        await session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy",
        "version": settings.app_version,
        "database": db_status,
    }


@router.get("/metrics")
async def get_metrics(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get system metrics."""
    queue_repo = QueueRepository(session)
    chat_repo = ChatRepository(session)
    source_repo = SourceRepository(session)

    queue_stats = await queue_repo.get_queue_stats()
    total_chats = await chat_repo.count()
    sources = await source_repo.get_all()

    return {
        "total_chats": total_chats,
        "queue_pending": queue_stats.get("pending", 0),
        "queue_processing": queue_stats.get("processing", 0),
        "queue_validated": queue_stats.get("validated", 0),
        "queue_indexed": queue_stats.get("indexed", 0),
        "queue_error": queue_stats.get("error", 0),
        "active_sources": len([s for s in sources if s.is_enabled]),
        "total_sources": len(sources),
    }


@router.get("/activity")
async def get_activity(limit: int = 50) -> list[dict]:
    """Get recent activity log."""
    return list(reversed(_activity_log[-limit:]))


@router.get("/activity/log")
async def add_manual_activity(job: str = "manual", details: str = "") -> dict:
    """Add manual activity entry."""
    add_activity(job, "manual", {"details": details})
    return {"status": "ok"}
