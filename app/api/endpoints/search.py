"""Search API endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.repositories.chat_repository import ChatRepository
from app.api.schemas.search import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search_chats(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    chat_type: str | None = Query(None, description="Filter by chat type"),
    language: str | None = Query(None, description="Filter by language"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    """Search Telegram chats and channels."""
    chat_repo = ChatRepository(session)

    offset = (page - 1) * size
    chats, total = await chat_repo.search_fts(
        query=q,
        chat_type=chat_type,
        language=language,
        offset=offset,
        limit=size,
    )

    pages = (total + size - 1) // size if total > 0 else 0

    return SearchResponse(
        items=[chat.__dict__ for chat in chats],
        total=total,
        page=page,
        size=size,
        pages=pages,
        query=q,
    )
