"""Search engine source for URL discovery."""

import asyncio

import structlog
from ddgs import DDGS

from app.utils.url_utils import extract_telegram_links

from .base_source import BaseSource

logger = structlog.get_logger()


class SearchEngineSource(BaseSource):
    """Discovers Telegram links via search engines."""

    SEARCH_QUERIES = [
        # English
        "telegram channel invite link",
        "telegram group join link",
        "t.me channel",
        "t.me group",
        "telegram chat link",
        "join telegram channel",
        "telegram community link",
        # Russian
        "ссылка на телеграм канал",
        "ссылка на телеграм группу",
        "телеграм чат ссылка",
        "присоединиться телеграм",
        "телеграм сообщество",
        # Specific topics
        "telegram crypto channel",
        "telegram programming group",
        "telegram news channel",
        "telegram anime chat",
        "telegram gaming group",
        "telegram music channel",
        "telegram trading group",
        "telegram tech channel",
        "telegram education group",
        "telegram business channel",
    ]

    def __init__(
        self,
        name: str = "search_engine",
        config: dict | None = None,
    ) -> None:
        super().__init__(name, config)
        cfg = config or {}
        self.queries = cfg.get("queries", self.SEARCH_QUERIES)
        self.max_results = cfg.get("max_results", 30)

    async def discover(self) -> list[str]:
        """Discover URLs via DuckDuckGo search."""
        all_urls = []

        ddgs = DDGS()

        # Run all queries in parallel (in batches of 5)
        batch_size = 5
        for i in range(0, len(self.queries), batch_size):
            batch = self.queries[i:i + batch_size]
            tasks = [self._search_safe(ddgs, query) for query in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result, query in zip(results, batch):
                if isinstance(result, Exception):
                    logger.error("search_failed", query=query, error=str(result))
                else:
                    all_urls.extend(result)
                    logger.debug("search_completed", query=query, found=len(result))

            # Small delay between batches
            await asyncio.sleep(1)

        unique_urls = list(set(all_urls))
        logger.info("search_engine_completed", queries=len(self.queries), found=len(unique_urls))
        return unique_urls

    async def _search_safe(self, ddgs: DDGS, query: str) -> list[str]:
        """Safe wrapper for search."""
        try:
            return self._search(ddgs, query)
        except Exception as e:
            logger.error("search_error", query=query, error=str(e))
            return []

    def _search(self, ddgs: DDGS, query: str) -> list[str]:
        """Perform search and extract Telegram links."""
        urls = []

        try:
            results = ddgs.text(query, max_results=self.max_results)

            for result in results:
                # Extract from URL
                href = result.get("href", "")
                links = extract_telegram_links(href)
                urls.extend(links)

                # Extract from body
                body = result.get("body", "")
                links = extract_telegram_links(body)
                urls.extend(links)

        except Exception as e:
            logger.error("ddgs_error", error=str(e))

        return urls
