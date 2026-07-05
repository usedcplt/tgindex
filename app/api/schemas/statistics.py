"""Statistics API schemas."""

from pydantic import BaseModel


class SourceStats(BaseModel):
    """Source statistics schema."""

    id: int
    name: str
    source_type: str
    total_found: int
    total_errors: int
    last_run_at: str | None = None
    is_enabled: bool


class StatisticsResponse(BaseModel):
    """Statistics response schema."""

    total_chats: int
    new_today: int
    new_this_week: int
    new_this_month: int
    processed_urls: int
    queue_size: int
    error_count: int
    duplicate_count: int
    broken_links: int
    avg_discovery_speed: float
    avg_indexing_speed: float
    flood_wait_count: int
    source_stats: list[SourceStats] | None = None
