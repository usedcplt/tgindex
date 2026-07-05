"""Main crawler service orchestrator."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crawler.base_source import BaseSource
from app.repositories.queue_repository import QueueRepository
from app.services.deduplicator import Deduplicator
from app.services.normalizer import Normalizer

logger = structlog.get_logger()


class CrawlerService:
    """Main crawler orchestrator."""

    def __init__(
        self,
        session: AsyncSession,
        sources: list[BaseSource],
    ) -> None:
        self.session = session
        self.sources = sources
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator(session)
        self.queue_repo = QueueRepository(session)

    async def run_discovery(self) -> dict:
        """Run discovery from all enabled sources."""
        total_found = 0
        total_new = 0
        errors = 0

        for source in self.sources:
            try:
                logger.info("running_source", source=source.name)
                urls = await source.discover()
                found_count = len(urls)
                total_found += found_count

                new_count = await self._process_urls_batch(urls, source.name)
                total_new += new_count

                logger.info(
                    "source_completed",
                    source=source.name,
                    found=found_count,
                    new=new_count,
                )
            except Exception as e:
                errors += 1
                logger.error("source_failed", source=source.name, error=str(e))

        return {
            "total_found": total_found,
            "total_new": total_new,
            "errors": errors,
        }

    async def _process_urls_batch(self, urls: list[str], source_name: str) -> int:
        """Process discovered URLs using bulk insert."""
        items = []

        for url in urls:
            normalized = self.normalizer.normalize(url)
            if not normalized:
                continue

            public_url = self.normalizer.to_public_url(normalized)
            items.append({
                "url": url,
                "normalized_url": public_url,
            })

        if not items:
            return 0

        return await self.deduplicator.add_batch(items, source=source_name)
