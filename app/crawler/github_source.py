"""GitHub source for URL discovery."""

import base64
import os
import asyncio

import httpx
import structlog

from app.utils.url_utils import extract_telegram_links

from .base_source import BaseSource

logger = structlog.get_logger()


class GitHubSource(BaseSource):
    """Discovers Telegram links from GitHub repositories."""

    SEARCH_QUERIES = [
        "telegram channel list",
        "telegram group list",
        "t.me",
        "telegram chat",
        "best telegram channels",
        "awesome telegram",
        "telegram resources",
    ]

    def __init__(
        self,
        name: str = "github",
        config: dict | None = None,
    ) -> None:
        super().__init__(name, config)
        cfg = config or {}
        self.queries = cfg.get("queries", self.SEARCH_QUERIES)
        self.max_results = cfg.get("max_results", 20)
        self.token = os.getenv("GITHUB_TOKEN")
        self._rate_limited_until = 0

    def _get_headers(self) -> dict:
        """Get headers with optional auth."""
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    async def discover(self) -> list[str]:
        """Discover URLs from GitHub."""
        if asyncio.get_event_loop().time() < self._rate_limited_until:
            return []

        all_urls = []

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers=self._get_headers(),
        ) as client:
            for query in self.queries:
                try:
                    urls = await self._search_code(client, query)
                    all_urls.extend(urls)
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error("github_search_failed", query=query, error=str(e))

        unique_urls = list(set(all_urls))
        logger.info("github_completed", queries=len(self.queries), found=len(unique_urls))
        return unique_urls

    async def _search_code(self, client: httpx.AsyncClient, query: str) -> list[str]:
        """Search GitHub code for Telegram links."""
        urls = []

        search_url = "https://api.github.com/search/code"
        params = {
            "q": f"{query} in:file extension:md",
            "per_page": min(self.max_results, 100),
        }

        response = await client.get(search_url, params=params)

        if response.status_code == 403:
            self._rate_limited_until = asyncio.get_event_loop().time() + 600
            return urls

        if response.status_code == 401:
            return urls

        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])

        for item in items:
            content_url = item.get("url")
            if content_url:
                file_urls = await self._fetch_file_content(client, content_url)
                urls.extend(file_urls)

        return urls

    async def _fetch_file_content(
        self, client: httpx.AsyncClient, url: str
    ) -> list[str]:
        """Fetch file content and extract Telegram links."""
        urls = []

        try:
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()
            content = data.get("content", "")

            if content:
                decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
                telegram_links = extract_telegram_links(decoded)
                urls.extend(telegram_links)

        except Exception as e:
            logger.error("file_fetch_failed", url=url, error=str(e))

        return urls
