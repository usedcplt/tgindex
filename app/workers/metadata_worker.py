"""Metadata extraction worker."""

import asyncio

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.repositories.queue_repository import QueueRepository
from app.services.metadata_service import MetadataService
from app.telegram.metadata_extractor import MetadataExtractor
from app.telegram.rate_limiter import RateLimiter

logger = structlog.get_logger()

# Shared instances
_metadata_extractor: MetadataExtractor | None = None
_rate_limiter: RateLimiter | None = None


def _get_metadata_extractor() -> MetadataExtractor:
    global _metadata_extractor
    if _metadata_extractor is None:
        _metadata_extractor = MetadataExtractor()
    return _metadata_extractor


def _get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


class MetadataWorker:
    """Worker for extracting metadata from validated URLs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.queue_repo = QueueRepository(session)
        self.metadata_extractor = _get_metadata_extractor()
        self.rate_limiter = _get_rate_limiter()
        self.metadata_service = MetadataService(
            session, self.metadata_extractor, self.rate_limiter
        )

    async def run(self) -> dict:
        """Run metadata extraction on validated URLs."""
        logger.info("metadata_worker_started")

        try:
            # Get VALIDATED URLs, not pending
            validated = await self.queue_repo.get_validated_batch(
                settings.crawler.batch_size
            )

            if not validated:
                logger.info("no_validated_urls")
                return {"processed": 0}

            urls = [item.url for item in validated]
            ids = [item.id for item in validated]

            # Mark as processing
            await self.queue_repo.mark_processing(ids)

            # Process URLs in parallel
            tasks = [self.metadata_service.extract_and_store(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            indexed_ids = []
            error_ids = []

            for result, item_id in zip(results, ids):
                if isinstance(result, Exception):
                    error_ids.append(item_id)
                elif result.get("success"):
                    indexed_ids.append(item_id)
                else:
                    error_ids.append(item_id)

            if indexed_ids:
                await self.queue_repo.mark_indexed(indexed_ids)
            if error_ids:
                await self.queue_repo.mark_error(error_ids, "Metadata extraction failed")

            logger.info(
                "metadata_worker_completed",
                total=len(validated),
                indexed=len(indexed_ids),
                errors=len(error_ids),
            )

            return {
                "processed": len(validated),
                "indexed": len(indexed_ids),
                "errors": len(error_ids),
            }

        except Exception as e:
            logger.error("metadata_worker_failed", error=str(e))
            raise
