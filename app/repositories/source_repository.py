"""Source repository."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import DiscoverySource

from .base import BaseRepository


class SourceRepository(BaseRepository[DiscoverySource]):
    """Source repository with specialized queries."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DiscoverySource)

    async def get_by_name(self, name: str) -> DiscoverySource | None:
        """Get source by name."""
        result = await self.session.execute(
            select(DiscoverySource).where(DiscoverySource.name == name)
        )
        return result.scalar_one_or_none()

    async def get_enabled_sources(self) -> list[DiscoverySource]:
        """Get all enabled sources."""
        result = await self.session.execute(
            select(DiscoverySource).where(DiscoverySource.is_enabled == True)
        )
        return list(result.scalars().all())

    async def get_sources_for_run(self) -> list[DiscoverySource]:
        """Get sources that need to run."""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(DiscoverySource)
            .where(DiscoverySource.is_enabled == True)
            .where(
                (DiscoverySource.next_run_at <= now) | (DiscoverySource.next_run_at.is_(None))
            )
            .order_by(DiscoverySource.next_run_at.asc().nullsfirst())
        )
        return list(result.scalars().all())

    async def update_run_stats(
        self,
        source_id: int,
        found_count: int,
        error_count: int = 0,
    ) -> None:
        """Update source run statistics."""
        source = await self.get_by_id(source_id)
        if source:
            source.last_run_at = datetime.utcnow()
            source.next_run_at = datetime.utcnow() + source.run_interval
            source.total_found += found_count
            source.total_errors += error_count
            await self.session.flush()

    async def get_source_stats(self) -> list[dict]:
        """Get statistics for all sources."""
        result = await self.session.execute(select(DiscoverySource))
        sources = result.scalars().all()

        return [
            {
                "id": s.id,
                "name": s.name,
                "source_type": s.source_type,
                "total_found": s.total_found,
                "total_errors": s.total_errors,
                "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
                "is_enabled": s.is_enabled,
            }
            for s in sources
        ]
