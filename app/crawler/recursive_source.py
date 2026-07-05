"""Recursive source for URL discovery from existing chats."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chat_repository import ChatRepository
from app.utils.url_utils import extract_telegram_links

from .base_source import BaseSource

logger = structlog.get_logger()


class RecursiveSource(BaseSource):
    """Discovers Telegram links from already indexed chats."""

    def __init__(
        self,
        session: AsyncSession,
        name: str = "recursive",
        config: dict | None = None,
    ) -> None:
        super().__init__(name, config)
        self.session = session
        self.chat_repo = ChatRepository(session)
        cfg = config or {}
        self.max_chats = cfg.get("max_chats", 1000)

    async def discover(self) -> list[str]:
        """Discover URLs from existing chat descriptions."""
        all_urls = []

        chats = await self.chat_repo.get_all(limit=self.max_chats)

        for chat in chats:
            if chat.description:
                links = extract_telegram_links(chat.description)
                all_urls.extend(links)

        logger.info("recursive_discovery_completed", chats_scanned=len(chats), found=len(all_urls))

        return list(set(all_urls))
