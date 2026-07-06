"""Rate limiter for Telegram API."""

import asyncio
import time

import structlog

from app.config import settings

logger = structlog.get_logger()


class RateLimiter:
    """Token bucket rate limiter for Telegram API."""

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.max_rate = settings.rate_limit.max_requests_per_second
        self.tokens = self.max_rate
        self.last_update = time.monotonic()
        self._flood_wait_until = 0

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        while True:
            async with self._lock:
                now = time.monotonic()

                # Check flood wait
                if now < self._flood_wait_until:
                    wait_time = self._flood_wait_until - now
                    logger.debug("flood_wait_active", seconds=wait_time)
                    # Release lock before sleeping
                    continue

                # Refill tokens
                elapsed = now - self.last_update
                self.tokens = min(self.max_rate, self.tokens + elapsed * self.max_rate)
                self.last_update = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return  # Got token, proceed

            # No token available - wait outside lock
            await asyncio.sleep(0.1)

    def handle_flood_wait(self, seconds: int) -> None:
        """Handle FloodWaitError from Telegram."""
        self._flood_wait_until = time.monotonic() + seconds
        logger.warning("flood_wait_handled", seconds=seconds)

    def reset(self) -> None:
        """Reset rate limiter."""
        self.tokens = self.max_rate
        self.last_update = time.monotonic()
        self._flood_wait_until = 0
