"""Link validation service."""

import asyncio

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from telethon.errors import FloodWaitError

from app.repositories.queue_repository import QueueRepository
from app.telegram.client import TelegramClient
from app.telegram.rate_limiter import RateLimiter
from app.utils.url_utils import extract_username

logger = structlog.get_logger()

# Shared instances
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


class Validator:
    """Validates Telegram links with retry logic."""

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session
        self.queue_repo = QueueRepository(session)
        self.telegram_client = _get_telegram_client()
        self.rate_limiter = _get_rate_limiter()

    async def validate_url(self, url: str, retries: int = 3) -> dict:
        """Validate a single Telegram URL with retry logic."""
        username = extract_username(url)
        if not username:
            return {
                "url": url,
                "is_valid": False,
                "data": None,
                "error": "Invalid URL format",
            }

        for attempt in range(retries):
            try:
                await self.rate_limiter.acquire()
                result = await self.telegram_client.check_username(username)

                if result is not None:
                    return {
                        "url": url,
                        "is_valid": True,
                        "data": result,
                        "error": None,
                    }
                else:
                    # Username not found or private - not an error, just invalid
                    return {
                        "url": url,
                        "is_valid": False,
                        "data": None,
                        "error": None,
                    }

            except FloodWaitError as e:
                # Handle flood wait - pause and retry
                self.rate_limiter.handle_flood_wait(e.seconds)
                logger.warning("flood_wait_retry", url=url, seconds=e.seconds, attempt=attempt)
                await asyncio.sleep(e.seconds)
                continue

            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(1)
                    continue
                return {
                    "url": url,
                    "is_valid": False,
                    "data": None,
                    "error": str(e),
                }

        return {
            "url": url,
            "is_valid": False,
            "data": None,
            "error": "Max retries exceeded",
        }

    async def validate_batch(self, urls: list[str]) -> list[dict]:
        """Validate batch of URLs in parallel."""
        tasks = [self.validate_url(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
