"""Validation worker."""

import asyncio

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.repositories.queue_repository import QueueRepository
from app.services.validator import Validator
from app.telegram.client import TelegramClient
from app.telegram.rate_limiter import RateLimiter

logger = structlog.get_logger()

# Shared instances to avoid creating new connections
_telegram_client: TelegramClient | None = None
_rate_limiter: RateLimiter | None = None


def _get_telegram_client() -> TelegramClient:
    global _telegram_client
    if _telegram_client is None:
        _telegram_client = TelegramClient()
    return _telegram_client


def _get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


class ValidationWorker:
    """Worker for validating Telegram URLs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.queue_repo = QueueRepository(session)
        self.telegram_client = _get_telegram_client()
        self.rate_limiter = _get_rate_limiter()
        self.validator = Validator(session, self.telegram_client, self.rate_limiter)

    async def run(self) -> dict:
        """Run validation on pending URLs."""
        logger.info("validation_worker_started")

        try:
            pending = await self.queue_repo.get_pending_batch(
                settings.crawler.batch_size
            )

            if not pending:
                logger.info("no_pending_urls")
                return {"processed": 0}

            urls = [item.url for item in pending]
            ids = [item.id for item in pending]

            await self.queue_repo.mark_processing(ids)

            # Process URLs in parallel (limited by rate limiter)
            tasks = [self.validator.validate_url(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            validated_ids = []
            invalid_ids = []

            for result, item_id in zip(results, ids):
                if isinstance(result, Exception):
                    invalid_ids.append(item_id)
                elif result.get("is_valid"):
                    validated_ids.append(item_id)
                else:
                    invalid_ids.append(item_id)

            if validated_ids:
                await self.queue_repo.mark_validated(validated_ids)
            if invalid_ids:
                await self.queue_repo.mark_invalid(invalid_ids)

            logger.info(
                "validation_worker_completed",
                total=len(pending),
                valid=len(validated_ids),
                invalid=len(invalid_ids),
            )

            return {
                "processed": len(pending),
                "valid": len(validated_ids),
                "invalid": len(invalid_ids),
            }

        except Exception as e:
            logger.error("validation_worker_failed", error=str(e))
            raise
