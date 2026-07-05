"""Discovery worker."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crawler.base_source import BaseSource
from app.services.crawler_service import CrawlerService

logger = structlog.get_logger()


class DiscoveryWorker:
    """Worker for discovering new Telegram URLs."""

    def __init__(
        self,
        session: AsyncSession,
        sources: list[BaseSource],
    ) -> None:
        self.session = session
        self.sources = sources
        self.crawler_service = CrawlerService(session, sources)

    async def run(self) -> dict:
        """Run discovery from all sources."""
        logger.info("discovery_worker_started")

        try:
            result = await self.crawler_service.run_discovery()
            logger.info("discovery_worker_completed", **result)
            return result
        except Exception as e:
            logger.error("discovery_worker_failed", error=str(e))
            raise
