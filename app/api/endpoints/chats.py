"""Chats API endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.repositories.chat_repository import ChatRepository
from app.api.schemas.chat import ChatResponse, ChatListResponse

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=ChatListResponse)
async def list_chats(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    chat_type: str | None = Query(None, description="Filter by chat type"),
    language: str | None = Query(None, description="Filter by language"),
    session: AsyncSession = Depends(get_session),
) -> ChatListResponse:
    """List all indexed chats."""
    chat_repo = ChatRepository(session)

    offset = (page - 1) * size
    chats = await chat_repo.get_all(offset=offset, limit=size)
    total = await chat_repo.count()

    pages = (total + size - 1) // size if total > 0 else 0

    return ChatListResponse(
        items=[ChatResponse.model_validate(chat) for chat in chats],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{telegram_id}", response_model=ChatResponse)
async def get_chat(
    telegram_id: int,
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """Get chat by Telegram ID."""
    chat_repo = ChatRepository(session)

    chat = await chat_repo.get_by_telegram_id(telegram_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return ChatResponse.model_validate(chat)
