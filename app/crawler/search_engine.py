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
        "telegram channel",
        "telegram group",
        "t.me",
        "telegram chat invite",
        "telegram community",
    ]

    def __init__(
        self,
        name: str = "search_engine",
        config: dict | None = None,
    ) -> None:
        super().__init__(name, config)
        cfg = config or {}
        self.queries = cfg.get("queries", self.SEARCH_QUERIES)
        self.max_results = cfg.get("max_results", 20)

    async def discover(self) -> list[str]:
        """Discover URLs via DuckDuckGo search."""
        all_urls = []

        ddgs = DDGS()

        # Run all queries in parallel
        tasks = [
            self._search_safe(ddgs, query)
            for query in self.queries
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result, query in zip(results, self.queries):
            if isinstance(result, Exception):
                logger.error("search_failed", query=query, error=str(result))
            else:
                all_urls.extend(result)
                logger.info("search_completed", query=query, found=len(result))

        return list(set(all_urls))

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
