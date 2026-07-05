"""Statistics snapshot model."""

from datetime import date, datetime

from sqlalchemy import DATE, DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class StatisticsSnapshot(Base):
    """Statistics snapshot model."""

    __tablename__ = "statistics_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[date] = mapped_column(DATE, unique=True, nullable=False)
    total_chats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_this_week: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_this_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_urls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    queue_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    broken_links: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_discovery_speed: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_indexing_speed: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    flood_wait_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_stats: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<StatisticsSnapshot(id={self.id}, date={self.snapshot_date})>"
