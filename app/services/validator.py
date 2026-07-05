"""Link validation service."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.queue_repository import QueueRepository
from app.telegram.client import TelegramClient
from app.telegram.rate_limiter import RateLimiter
from app.utils.url_utils import extract_username

logger = structlog.get_logger()


class Validator:
    """Validates Telegram links."""

    def __init__(
        self,
        session: AsyncSession,
        telegram_client: TelegramClient,
        rate_limiter: RateLimiter,
    ) -> None:
        self.session = session
        self.queue_repo = QueueRepository(session)
        self.telegram_client = telegram_client
        self.rate_limiter = rate_limiter

    async def validate_url(self, url: str) -> dict:
        """Validate a single Telegram URL."""
        try:
            # Extract username from URL
            username = extract_username(url)
            if not username:
                logger.debug("invalid_url_format", url=url)
                return {
                    "url": url,
                    "is_valid": False,
                    "data": None,
                    "error": "Invalid URL format",
                }

            logger.debug("validating_url", url=url, username=username)
            await self.rate_limiter.acquire()

            result = await self.telegram_client.check_username(username)

            is_valid = result is not None
            logger.debug("validation_result", url=url, username=username, is_valid=is_valid)

            return {
                "url": url,
                "is_valid": is_valid,
                "data": result,
                "error": None,
            }
        except Exception as e:
            logger.error("validation_failed", url=url, error=str(e))
            return {
                "url": url,
                "is_valid": False,
                "data": None,
                "error": str(e),
            }

    async def validate_batch(self, urls: list[str]) -> list[dict]:
        """Validate batch of URLs."""
        results = []
        for url in urls:
            result = await self.validate_url(url)
            results.append(result)
        return results
