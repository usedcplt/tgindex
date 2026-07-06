"""Main crawler service orchestrator."""

import asyncio

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
        """Run discovery from all sources in parallel."""
        total_found = 0
        total_new = 0
        errors = 0

        # Run all sources in parallel
        tasks = [self._run_source(source) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result, source in zip(results, self.sources):
            if isinstance(result, Exception):
                errors += 1
                logger.error("source_failed", source=source.name, error=str(result))
            else:
                found, new = result
                total_found += found
                total_new += new

        return {
            "total_found": total_found,
            "total_new": total_new,
            "errors": errors,
        }

    async def _run_source(self, source: BaseSource) -> tuple[int, int]:
        """Run a single source and return (found, new) counts."""
        try:
            logger.info("running_source", source=source.name)
            urls = await source.discover()
            found_count = len(urls)

            new_count = await self._process_urls_batch(urls, source.name)

            logger.info(
                "source_completed",
                source=source.name,
                found=found_count,
                new=new_count,
            )

            return found_count, new_count
        except Exception as e:
            logger.error("source_error", source=source.name, error=str(e))
            return 0, 0

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
