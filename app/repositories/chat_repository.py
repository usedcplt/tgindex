"""Chat repository with FTS search."""

from datetime import datetime, timedelta

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import FTS_LANGUAGE
from app.models.chat import Chat

from .base import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    """Chat repository with FTS search and specialized queries."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Chat)

    async def get_by_telegram_id(self, telegram_id: int) -> Chat | None:
        """Get chat by Telegram ID."""
        result = await self.session.execute(
            select(Chat).where(Chat.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Chat | None:
        """Get chat by username."""
        result = await self.session.execute(
            select(Chat).where(Chat.username == username)
        )
        return result.scalar_one_or_none()

    async def search_fts(
        self,
        query: str,
        chat_type: str | None = None,
        language: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Chat], int]:
        """Full-text search with filters."""
        ts_query = func.plainto_tsquery(FTS_LANGUAGE, query)
        ts_vector = func.to_tsvector(
            FTS_LANGUAGE,
            func.coalesce(Chat.title, "")
            + " "
            + func.coalesce(Chat.description, "")
            + " "
            + func.coalesce(Chat.topic, ""),
        )

        base_query = select(Chat).where(
            ts_vector.op("@@")(ts_query)
        )

        if chat_type:
            base_query = base_query.where(Chat.chat_type == chat_type)
        if language:
            base_query = base_query.where(Chat.language == language)

        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        ranked_query = base_query.order_by(
            func.ts_rank(ts_vector, ts_query).desc()
        ).offset(offset).limit(limit)

        result = await self.session.execute(ranked_query)
        chats = list(result.scalars().all())

        return chats, total

    async def get_chats_for_update(
        self,
        limit: int = 100,
    ) -> list[Chat]:
        """Get chats that need updating."""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(Chat)
            .where(Chat.is_active == True)
            .where((Chat.next_check_at <= now) | (Chat.next_check_at.is_(None)))
            .order_by(Chat.next_check_at.asc().nullsfirst())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_chats(self, days: int = 7, limit: int = 100) -> list[Chat]:
        """Get recently discovered chats."""
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(Chat)
            .where(Chat.discovered_at >= since)
            .order_by(Chat.discovered_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_statistics(self) -> dict:
        """Get chat statistics."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        total = await self.count()

        new_today = await self.session.execute(
            select(func.count()).where(Chat.discovered_at >= today_start)
        )
        new_this_week = await self.session.execute(
            select(func.count()).where(Chat.discovered_at >= week_start)
        )
        new_this_month = await self.session.execute(
            select(func.count()).where(Chat.discovered_at >= month_start)
        )

        return {
            "total_chats": total,
            "new_today": new_today.scalar_one(),
            "new_this_week": new_this_week.scalar_one(),
            "new_this_month": new_this_month.scalar_one(),
        }

    async def update_check_schedule(
        self,
        chat_id: int,
        next_check_at: datetime,
    ) -> None:
        """Update next check time for a chat."""
        await self.session.execute(
            select(Chat).where(Chat.id == chat_id)
        )
        chat = await self.get_by_id(chat_id)
        if chat:
            chat.next_check_at = next_check_at
            chat.last_checked_at = datetime.utcnow()
            await self.session.flush()
