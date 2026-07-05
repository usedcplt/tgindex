"""Crawl log model."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CrawlLog(Base):
    """Crawl history log model."""

    __tablename__ = "crawl_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), nullable=True
    )
    source_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("discovery_sources.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_crawl_logs_chat_id", "chat_id"),
        Index("idx_crawl_logs_created_at", "created_at"),
        Index("idx_crawl_logs_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<CrawlLog(id={self.id}, action='{self.action}', status='{self.status}')>"
