"""Chat API schemas."""

from datetime import datetime

from pydantic import BaseModel


class ChatResponse(BaseModel):
    """Chat response schema."""

    id: int
    telegram_id: int
    username: str | None = None
    public_url: str | None = None
    title: str
    description: str | None = None
    chat_type: str
    member_count: int = 0
    language: str | None = None
    topic: str | None = None
    discovery_source: str | None = None
    discovered_at: datetime
    last_checked_at: datetime | None = None
    quality_score: float = 0.0
    popularity_score: float = 0.0
    activity_score: float = 0.0
    growth_score: float = 0.0
    health_score: float = 0.0
    is_active: bool = True

    model_config = {"from_attributes": True}


class ChatListResponse(BaseModel):
    """Chat list response schema."""

    items: list[ChatResponse]
    total: int
    page: int
    size: int
    pages: int
