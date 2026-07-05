"""Statistics repository."""

from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.statistics import StatisticsSnapshot
from app.models.url_queue import UrlQueue

from .base import BaseRepository


class StatsRepository(BaseRepository[StatisticsSnapshot]):
    """Statistics repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, StatisticsSnapshot)

    async def get_or_create_today(self) -> StatisticsSnapshot:
        """Get or create today's statistics snapshot."""
        today = date.today()
        result = await self.session.execute(
            select(StatisticsSnapshot).where(StatisticsSnapshot.snapshot_date == today)
        )
        snapshot = result.scalar_one_or_none()

        if not snapshot:
            snapshot = StatisticsSnapshot(snapshot_date=today)
            self.session.add(snapshot)
            await self.session.flush()

        return snapshot

    async def update_statistics(self) -> StatisticsSnapshot:
        """Update current statistics."""
        snapshot = await self.get_or_create_today()

        # Count chats
        total_result = await self.session.execute(select(func.count(Chat.id)))
        snapshot.total_chats = total_result.scalar_one()

        # Count new today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        new_today_result = await self.session.execute(
            select(func.count(Chat.id)).where(Chat.discovered_at >= today_start)
        )
        snapshot.new_today = new_today_result.scalar_one()

        # Count new this week
        week_start = today_start - timedelta(days=7)
        new_week_result = await self.session.execute(
            select(func.count(Chat.id)).where(Chat.discovered_at >= week_start)
        )
        snapshot.new_this_week = new_week_result.scalar_one()

        # Count new this month
        month_start = today_start - timedelta(days=30)
        new_month_result = await self.session.execute(
            select(func.count(Chat.id)).where(Chat.discovered_at >= month_start)
        )
        snapshot.new_this_month = new_month_result.scalar_one()

        # Queue stats
        queue_result = await self.session.execute(
            select(func.count(UrlQueue.id)).where(UrlQueue.status == "pending")
        )
        snapshot.queue_size = queue_result.scalar_one()

        # Error count
        error_result = await self.session.execute(
            select(func.count(UrlQueue.id)).where(UrlQueue.status == "error")
        )
        snapshot.error_count = error_result.scalar_one()

        await self.session.flush()
        return snapshot

    async def get_statistics(self) -> dict:
        """Get current statistics."""
        snapshot = await self.update_statistics()
        queue_stats_result = await self.session.execute(
            select(
                UrlQueue.status,
                func.count(UrlQueue.id),
            ).group_by(UrlQueue.status)
        )
        queue_stats = {row[0]: row[1] for row in queue_stats_result.all()}

        return {
            "total_chats": snapshot.total_chats,
            "new_today": snapshot.new_today,
            "new_this_week": snapshot.new_this_week,
            "new_this_month": snapshot.new_this_month,
            "processed_urls": queue_stats.get("indexed", 0) + queue_stats.get("invalid", 0),
            "queue_size": queue_stats.get("pending", 0),
            "error_count": queue_stats.get("error", 0),
            "duplicate_count": 0,
            "broken_links": queue_stats.get("invalid", 0),
            "avg_discovery_speed": 0.0,
            "avg_indexing_speed": 0.0,
            "flood_wait_count": 0,
        }

    async def get_historical_statistics(self, days: int = 30) -> list[dict]:
        """Get historical statistics."""
        since = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(StatisticsSnapshot)
            .where(StatisticsSnapshot.snapshot_date >= since)
            .order_by(StatisticsSnapshot.snapshot_date.asc())
        )
        snapshots = result.scalars().all()

        return [
            {
                "date": s.snapshot_date.isoformat(),
                "total_chats": s.total_chats,
                "new_today": s.new_today,
            }
            for s in snapshots
        ]
