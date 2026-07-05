"""Metadata extractor for Telegram entities."""

import hashlib

import structlog

from app.utils.url_utils import extract_username

from .client import TelegramClient
from .rate_limiter import RateLimiter

logger = structlog.get_logger()


class MetadataExtractor:
    """Extracts metadata from Telegram entities."""

    def __init__(self) -> None:
        self.client = TelegramClient()
        self.rate_limiter = RateLimiter()

    async def extract(self, url: str) -> dict | None:
        """Extract metadata from Telegram URL."""
        username = extract_username(url)
        if not username:
            return None

        return await self._extractByUsername(username)

    async def extract_by_id(
        self, telegram_id: int, access_hash: int
    ) -> dict | None:
        """Extract metadata by Telegram ID."""
        try:
            await self.rate_limiter.acquire()
            await self.client.connect()

            entity = await self.client.client.get_entity(telegram_id)

            return self._build_metadata(entity)

        except Exception as e:
            logger.error("extract_by_id_failed", telegram_id=telegram_id, error=str(e))
            return None

    async def _extractByUsername(self, username: str) -> dict | None:
        """Extract metadata by username."""
        try:
            await self.rate_limiter.acquire()
            info = await self.client.check_username(username)

            if not info:
                return None

            return {
                "telegram_id": info["telegram_id"],
                "access_hash": info["access_hash"],
                "username": info["username"],
                "public_url": f"https://t.me/{info['username']}",
                "title": info.get("title", ""),
                "description": info.get("description"),
                "chat_type": info.get("chat_type", "channel"),
                "member_count": info.get("member_count", 0),
                "avatar_hash": None,
            }

        except Exception as e:
            logger.error("extractByUsername_failed", username=username, error=str(e))
            return None

    def _build_metadata(self, entity) -> dict:
        """Build metadata dict from entity."""
        avatar_hash = None
        if hasattr(entity, "photo") and entity.photo:
            avatar_hash = hashlib.md5(str(entity.photo).encode()).hexdigest()

        return {
            "telegram_id": entity.id,
            "access_hash": entity.access_hash,
            "username": getattr(entity, "username", None),
            "public_url": f"https://t.me/{getattr(entity, 'username', '')}" if getattr(entity, "username", None) else None,
            "title": getattr(entity, "title", None) or getattr(entity, "first_name", ""),
            "description": getattr(entity, "about", None),
            "chat_type": self._get_chat_type(entity),
            "member_count": getattr(entity, "participants_count", None) or 0,
            "avatar_hash": avatar_hash,
        }

    def _get_chat_type(self, entity) -> str:
        """Determine chat type."""
        if hasattr(entity, "megagroup") and entity.megagroup:
            return "supergroup"
        elif hasattr(entity, "broadcast") and entity.broadcast:
            return "channel"
        return "group"
