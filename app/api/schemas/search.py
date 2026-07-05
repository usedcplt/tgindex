"""Search API schemas."""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Search request schema."""

    q: str = Field(..., min_length=1, max_length=200, description="Search query")
    chat_type: str | None = Field(None, description="Filter by chat type")
    language: str | None = Field(None, description="Filter by language")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")


class SearchResponse(BaseModel):
    """Search response schema."""

    items: list[dict]
    total: int
    page: int
    size: int
    pages: int
    query: str
