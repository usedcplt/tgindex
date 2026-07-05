"""Rate limiter for Telegram API."""

import asyncio
import time

import structlog

from app.config import settings

logger = structlog.get_logger()


class RateLimiter:
    """Token bucket rate limiter for Telegram API."""

    def __init__(self) -> None:
        self.max_rate = settings.rate_limit.max_requests_per_second
        self.tokens = self.max_rate
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.max_rate, self.tokens + elapsed * self.max_rate)
            self.last_update = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.max_rate
                logger.debug("rate_limit_wait", seconds=wait_time)
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1

    def reset(self) -> None:
        """Reset rate limiter."""
        self.tokens = self.max_rate
        self.last_update = time.monotonic()
