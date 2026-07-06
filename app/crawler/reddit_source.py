"""Reddit source for URL discovery."""

import httpx
import structlog

from app.utils.url_utils import extract_telegram_links

from .base_source import BaseSource

logger = structlog.get_logger()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


class RedditSource(BaseSource):
    """Discovers Telegram links from Reddit."""

    SUBREDDITS = [
        "telegram",
        "TelegramGroups",
        "TelegramChannels",
        "telegramchat",
        "RussianTelegram",
        "TelegramPromote",
    ]

    def __init__(
        self,
        name: str = "reddit",
        config: dict | None = None,
    ) -> None:
        super().__init__(name, config)
        cfg = config or {}
        self.subreddits = cfg.get("subreddits", self.SUBREDDITS)
        self.max_posts = cfg.get("max_posts", 50)

    async def discover(self) -> list[str]:
        """Discover URLs from Reddit."""
        all_urls = []

        async with httpx.AsyncClient(
            timeout=30,
            headers=HEADERS,
        ) as client:
            for subreddit in self.subreddits:
                try:
                    urls = await self._scrape_subreddit(client, subreddit)
                    all_urls.extend(urls)
                    logger.info("reddit_scraped", subreddit=subreddit, found=len(urls))
                except Exception as e:
                    logger.error("reddit_failed", subreddit=subreddit, error=str(e))

        return list(set(all_urls))

    async def _scrape_subreddit(self, client: httpx.AsyncClient, subreddit: str) -> list[str]:
        """Scrape a subreddit for Telegram links."""
        urls = []

        # Use old.reddit.com for easier scraping
        url = f"https://old.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": "t.me OR telegram",
            "restrict_sr": "true",
            "sort": "new",
            "limit": self.max_posts,
        }

        response = await client.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            posts = data.get("data", {}).get("children", [])

            for post in posts:
                post_data = post.get("data", {})
                # Check title and selftext
                text = f"{post_data.get('title', '')} {post_data.get('selftext', '')}"
                links = extract_telegram_links(text)
                urls.extend(links)

        return urls
