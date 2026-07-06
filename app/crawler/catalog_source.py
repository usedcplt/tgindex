"""Telegram catalog source for URL discovery."""

import asyncio

import httpx
import structlog
from bs4 import BeautifulSoup

from app.utils.url_utils import extract_telegram_links

from .base_source import BaseSource

logger = structlog.get_logger()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


class CatalogSource(BaseSource):
    """Discovers Telegram links from Telegram catalogs and directories."""

    CATALOG_URLS = [
        "https://t.me/s/channels",
        "https://t.me/s/chat",
        "https://t.me/s/groups",
        "https://t.me/s/newchannels",
        "https://t.me/s/BestChannelsInTelegram",
        "https://t.me/s/russian_telegram",
        "https://t.me/s/telegram_channels",
        "https://t.me/s/topchannels",
        "https://t.me/s/IT",
        "https://t.me/s/crypto",
        "https://t.me/s/news",
        "https://t.me/s/programming",
        "https://t.me/s/design",
        "https://t.me/s/music",
        "https://t.me/s/movies",
        "https://t.me/s/games",
        "https://t.me/s/sports",
        "https://t.me/s/education",
        "https://t.me/s/tech",
        "https://t.me/s/business",
        "https://t.me/s/science",
        "https://t.me/s/art",
        "https://t.me/s/photography",
        "https://t.me/s/travel",
        "https://t.me/s/food",
        "https://t.me/s/health",
        "https://t.me/s/fitness",
        "https://t.me/s/fashion",
        "https://t.me/s/cars",
        "https://t.me/s/reddit",
    ]

    def __init__(
        self,
        name: str = "catalog",
        config: dict | None = None,
    ) -> None:
        super().__init__(name, config)
        cfg = config or {}
        self.catalog_urls = cfg.get("urls", self.CATALOG_URLS)

    async def discover(self) -> list[str]:
        """Discover URLs from Telegram catalogs in parallel."""
        all_urls = []

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            # Scrape all catalogs in parallel (max 5 concurrent)
            semaphore = asyncio.Semaphore(5)

            async def scrape_with_limit(url):
                async with semaphore:
                    return await self._scrape_catalog_safe(client, url)

            tasks = [scrape_with_limit(url) for url in self.catalog_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result, url in zip(results, self.catalog_urls):
                if isinstance(result, Exception):
                    logger.debug("catalog_failed", url=url, error=str(result))
                elif result:
                    all_urls.extend(result)
                    logger.debug("catalog_scraped", url=url, found=len(result))

        unique_urls = list(set(all_urls))
        logger.info("catalog_total", urls_found=len(unique_urls))
        return unique_urls

    async def _scrape_catalog_safe(
        self, client: httpx.AsyncClient, url: str
    ) -> list[str]:
        """Safe wrapper for catalog scraping."""
        try:
            return await self._scrape_catalog(client, url)
        except Exception as e:
            logger.debug("catalog_error", url=url, error=str(e))
            return []

    async def _scrape_catalog(self, client: httpx.AsyncClient, url: str) -> list[str]:
        """Scrape a single catalog page."""
        urls = []

        response = await client.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Find all links that look like Telegram channels
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            telegram_links = extract_telegram_links(href)
            urls.extend(telegram_links)

        # Also check text content for t.me links
        text = soup.get_text()
        telegram_links = extract_telegram_links(text)
        urls.extend(telegram_links)

        return urls
