"""Common API schemas."""

from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    """Paginated response schema."""

    items: list
    total: int
    page: int
    size: int
    pages: int


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
    code: str | None = None
