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
        "telegram channel invite link",
        "telegram group join link",
        "t.me channel",
        "t.me group",
        "telegram chat link",
        "join telegram channel",
        "telegram community link",
        "best telegram channels",
        "cool telegram groups",
        "telegram channels list",
        "telegram groups list",
        "awesome telegram channels",
        "top telegram channels",
        "popular telegram channels",
        "telegram channel directory",
        "telegram links collection",
        "ссылка на телеграм канал",
        "ссылка на телеграм группу",
        "телеграм чат ссылка",
        "лучшие телеграм каналы",
        "интересные телеграм каналы",
        "топ телеграм каналов",
        "каталог телеграм каналов",
        "список телеграм каналов",
        "телеграм группа ссылка",
        "ссылки телеграм",
        "telegram crypto channel",
        "telegram bitcoin group",
        "telegram trading signals",
        "telegram programming channel",
        "telegram developer group",
        "telegram python chat",
        "telegram tech news",
        "telegram ai group",
        "telegram news channel",
        "telegram media channel",
        "telegram gaming channel",
        "telegram anime channel",
        "telegram music channel",
        "telegram business channel",
        "telegram education channel",
        "telegram health channel",
        "telegram fitness group",
        "telegram travel channel",
        "telegram food channel",
        "telegram art channel",
        "telegram design group",
        "telegram science channel",
        "telegram cars channel",
        "telegram jobs channel",
        "telegram freelance group",
        "telegram english learning",
        "telegram books channel",
        "telegram photography channel",
        "telegram linux group",
        "telegram web group",
        "telegram database group",
        "telegram cybersecurity channel",
        "telegram blockchain channel",
        "telegram real estate channel",
        "telegram parenting channel",
        "telegram pets channel",
        "telegram gardening channel",
        "telegram diy channel",
        "telegram podcast channel",
        "telegram writing channel",
        "telegram self improvement",
        "telegram meditation group",
        "telegram history channel",
        "telegram space channel",
        "telegram comedy channel",
        "telegram dating channel",
        "telegram fashion channel",
        "telegram tech reviews",
        "telegram gaming news",
        "telegram social media",
        "telegram freelancer tips",
        "telegram startup tips",
        "telegram marketing channel",
        "telegram seo group",
        "telegram ecommerce",
        "telegram affiliate marketing",
        "telegram stock tips",
        "telegram investment group",
        "telegram budgeting group",
        "telegram tax tips",
        "telegram online courses",
        "telegram coding bootcamp",
        "telegram interview tips",
        "telegram career growth",
        "telegram productivity tips",
        "telegram ai tools",
        "telegram chatgpt group",
        "telegram privacy tips",
        "telegram vpn group",
        "telegram ubuntu group",
        "telegram react group",
        "telegram nodejs group",
        "telegram docker group",
        "telegram kubernetes",
        "telegram machine learning",
        "telegram data science",
        "telegram iot group",
        "telegram web3 group",
        "telegram defi chat",
        "telegram nft group",
        "telegram vr group",
        "telegram quantum computing",
        "telegram nasa group",
        "telegram climate group",
        "telegram biotech group",
        "telegram telemedicine",
        "telegram fintech group",
        "telegram edtech group",
        "telegram cleantech group",
        "telegram developer tools",
        "telegram monitoring tools",
        "telegram ci/cd tools",
        "telegram security tools",
        "telegram cloud tools",
        "telegram ai tools group",
        "telegram productivity tools",
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

        batch_size = 10
        for i in range(0, len(self.queries), batch_size):
            batch = self.queries[i:i + batch_size]
            tasks = [self._search_safe(ddgs, query) for query in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result, query in zip(results, batch):
                if isinstance(result, Exception):
                    logger.error("search_failed", query=query, error=str(result))
                else:
                    all_urls.extend(result)

            await asyncio.sleep(2)

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
                href = result.get("href", "")
                links = extract_telegram_links(href)
                urls.extend(links)

                body = result.get("body", "")
                links = extract_telegram_links(body)
                urls.extend(links)

        except Exception as e:
            logger.error("ddgs_error", error=str(e))

        return urls
