"""Validation worker."""

import asyncio

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.repositories.queue_repository import QueueRepository
from app.services.validator import Validator

logger = structlog.get_logger()

# Shared validator instance
_validator: Validator | None = None


def _get_validator(session: AsyncSession) -> Validator:
    global _validator
    if _validator is None:
        _validator = Validator(session)
    return _validator


class ValidationWorker:
    """Worker for validating Telegram URLs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.queue_repo = QueueRepository(session)
        self.validator = _get_validator(session)

    async def run(self) -> dict:
        """Run validation on pending URLs."""
        logger.info("validation_worker_started")

        try:
            pending = await self.queue_repo.get_pending_batch(
                settings.crawler.batch_size
            )

            if not pending:
                logger.debug("no_pending_urls")
                return {"processed": 0}

            urls = [item.url for item in pending]
            ids = [item.id for item in pending]

            await self.queue_repo.mark_processing(ids)

            # Process URLs in parallel
            results = await self.validator.validate_batch(urls)

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
                "validation_completed",
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
            logger.error("validation_failed", error=str(e))
            raise
