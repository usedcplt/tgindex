"""Dashboard router."""

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.repositories.chat_repository import ChatRepository
from app.repositories.source_repository import SourceRepository
from app.repositories.stats_repository import StatsRepository
from app.repositories.queue_repository import QueueRepository

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="app/dashboard/templates")


@router.get("/")
async def dashboard_index(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Dashboard main page."""
    stats_repo = StatsRepository(session)
    stats = await stats_repo.get_statistics()

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "stats": stats},
    )


@router.get("/chats")
async def dashboard_chats(
    request: Request,
    page: int = 1,
    session: AsyncSession = Depends(get_session),
):
    """Dashboard chats list."""
    chat_repo = ChatRepository(session)
    size = 20
    offset = (page - 1) * size

    chats = await chat_repo.get_all(offset=offset, limit=size)
    total = await chat_repo.count()
    pages = (total + size - 1) // size if total > 0 else 0

    return templates.TemplateResponse(
        "chats.html",
        {
            "request": request,
            "chats": chats,
            "total": total,
            "page": page,
            "pages": pages,
        },
    )


@router.get("/sources")
async def dashboard_sources(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Dashboard sources page."""
    source_repo = SourceRepository(session)
    sources = await source_repo.get_all()

    return templates.TemplateResponse(
        "sources.html",
        {"request": request, "sources": sources},
    )


@router.get("/statistics")
async def dashboard_statistics(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Dashboard statistics page."""
    stats_repo = StatsRepository(session)
    stats = await stats_repo.get_statistics()
    history = await stats_repo.get_historical_statistics(30)

    return templates.TemplateResponse(
        "statistics.html",
        {"request": request, "stats": stats, "history": history},
    )


@router.get("/system")
async def dashboard_system(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Dashboard system page."""
    queue_repo = QueueRepository(session)
    queue_stats = await queue_repo.get_queue_stats()

    return templates.TemplateResponse(
        "system.html",
        {"request": request, "queue_stats": queue_stats},
    )
