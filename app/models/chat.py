"""Chat/Channel model."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Chat(Base):
    """Telegram chat or channel model."""

    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    access_hash: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    public_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    chat_type: Mapped[str] = mapped_column(String(20), nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    discovery_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    avatar_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    popularity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    activity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    growth_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    health_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_chats_username", "username", postgresql_where="username IS NOT NULL"),
        Index("idx_chats_type", "chat_type"),
        Index("idx_chats_language", "language", postgresql_where="language IS NOT NULL"),
        Index("idx_chats_topic", "topic", postgresql_where="topic IS NOT NULL"),
        Index("idx_chats_discovered_at", "discovered_at"),
        Index("idx_chats_next_check_at", "next_check_at", postgresql_where="next_check_at IS NOT NULL"),
        Index("idx_chats_quality_score", "quality_score"),
        Index("idx_chats_is_active", "is_active", postgresql_where="is_active = TRUE"),
        Index("idx_chats_member_count", "member_count"),
    )

    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, telegram_id={self.telegram_id}, title='{self.title}')>"
