"""Scheduler service for check scheduling."""

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.repositories.chat_repository import ChatRepository
from app.utils.time_utils import get_next_check_time


class SchedulerService:
    """Manages check scheduling for chats."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.chat_repo = ChatRepository(session)

    async def schedule_check(self, chat_id: int) -> None:
        """Schedule next check for a chat."""
        chat = await self.chat_repo.get_by_id(chat_id)
        if not chat:
            return

        next_check = get_next_check_time(
            chat.last_checked_at,
            chat.member_count,
            chat.health_score,
        )

        await self.chat_repo.update_check_schedule(chat_id, next_check)

    async def schedule_batch(self, chat_ids: list[int]) -> None:
        """Schedule checks for multiple chats."""
        for chat_id in chat_ids:
            await self.schedule_check(chat_id)

    async def get_chats_due_for_check(self, limit: int = 100) -> list[Chat]:
        """Get chats that are due for checking."""
        return await self.chat_repo.get_chats_for_update(limit)

    async def update_health_score(self, chat_id: int, score: float) -> None:
        """Update health score for a chat."""
        chat = await self.chat_repo.get_by_id(chat_id)
        if chat:
            chat.health_score = score
            await self.session.flush()
