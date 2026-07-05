"""Statistics service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stats_repository import StatsRepository


class StatisticsService:
    """Statistics aggregation service."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.stats_repo = StatsRepository(session)

    async def get_statistics(self) -> dict:
        """Get current statistics."""
        return await self.stats_repo.get_statistics()

    async def get_historical(self, days: int = 30) -> list[dict]:
        """Get historical statistics."""
        return await self.stats_repo.get_historical_statistics(days)

    async def update_statistics(self) -> dict:
        """Update and return current statistics."""
        await self.stats_repo.update_statistics()
        return await self.stats_repo.get_statistics()
