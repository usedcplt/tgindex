"""Telegram search source - uses Telegram's built-in search."""

import asyncio

import structlog
from telethon.errors import FloodWaitError

from app.telegram.client import TelegramClient
from app.telegram.rate_limiter import RateLimiter

from .base_source import BaseSource

logger = structlog.get_logger()


class TelegramSearchSource(BaseSource):
    """Discovers Telegram chats using Telegram's search API."""

    # Categories: prefix + "chat" or "канал"
    CATEGORIES_EN = [
        "anime", "crypto", "bitcoin", "ethereum", "nft", "defi",
        "python", "javascript", "coding", "programming", "developer",
        "gaming", "games", "esport", "steam",
        "news", "media", "press",
        "business", "startup", "marketing", "crypto",
        "tech", "technology", "ai", "machine learning",
        "music", "movies", "anime", "manga",
        "sports", "football", "basketball",
        "education", "learning", "course", "tutorial",
        "travel", "tourism", "vacation",
        "food", "cooking", "recipe",
        "health", "fitness", "workout",
        "fashion", "style", "beauty",
        "art", "design", "photo",
        "science", "physics", "chemistry",
        "cars", "auto", "motorsport",
        "crypto", "trading", "investing",
        "jobs", "freelance", "remote work",
        "english", "languages", "spanish",
        "books", "reading", "literature",
        "photography", "camera", "photo",
        "stocks", "forex", "economics",
        "linux", "windows", "mac",
        "android", "ios", "mobile",
        "web", "frontend", "backend",
        "database", "sql", "mongodb",
        "devops", "docker", "kubernetes",
        "cybersecurity", "hacking", "infosec",
    ]

    CATEGORIES_RU = [
        "анатомия", "криптовалюта", "биткоин", "нфт",
        "программирование", "кодинг", "разработка", "python",
        "игры", "гейминг", "киберспорт",
        "новости", "медиа", "пресса",
        "бизнес", "стартап", "маркетинг",
        "технологии", "айти", "искусственный интеллект",
        "музыка", "фильмы", "аниме", "манга",
        "спорт", "футбол", "баскетбол",
        "образование", "обучение", "курс",
        "путешествия", "туризм", "отдых",
        "еда", "кулинария", "рецепты",
        "здоровье", "фитнес", "тренировки",
        "мода", "стиль", "красота",
        "искусство", "дизайн", "фото",
        "наука", "физика", "химия",
        "автомобили", "авто", "моторспорт",
        "вакансии", "фриланс", "удалённая работа",
        "английский", "языки", "переводы",
        "книги", "чтение", "литература",
        "linux", "windows", "mac",
        "android", "ios", "мобильные",
        "веб", "фронтенд", "бэкенд",
        "базы данных", "sql", "mongodb",
        "девопс", "docker", "кибербезопасность",
    ]

    def __init__(
        self,
        name: str = "telegram_search",
        config: dict | None = None,
    ) -> None:
        super().__init__(name, config)
        cfg = config or {}
        self.categories_en = cfg.get("categories_en", self.CATEGORIES_EN)
        self.categories_ru = cfg.get("categories_ru", self.CATEGORIES_RU)
        self.max_per_category = cfg.get("max_per_category", 20)
        self._client: TelegramClient | None = None
        self._rate_limiter: RateLimiter | None = None

    async def discover(self) -> list[str]:
        """Discover Telegram chats using search."""
        from app.telegram.client import TelegramClient
        from app.telegram.rate_limiter import RateLimiter

        if self._client is None:
            self._client = TelegramClient()
        if self._rate_limiter is None:
            self._rate_limiter = RateLimiter()

        all_usernames = []

        # Combine English and Russian categories
        all_categories = self.categories_en + self.categories_ru

        # Search in batches to avoid rate limits
        for category in all_categories:
            try:
                usernames = await self._search_category(category)
                all_usernames.extend(usernames)
                logger.debug("category_searched", category=category, found=len(usernames))
            except FloodWaitError as e:
                logger.warning("flood_wait_category", category=category, seconds=e.seconds)
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logger.debug("category_failed", category=category, error=str(e))

            # Small delay between categories
            await asyncio.sleep(0.5)

        # Convert usernames to URLs
        urls = [f"https://t.me/{username}" for username in all_usernames if username]
        unique_urls = list(set(urls))

        logger.info("telegram_search_completed", categories=len(all_categories), found=len(unique_urls))
        return unique_urls

    async def _search_category(self, category: str) -> list[str]:
        """Search for chats in a category."""
        usernames = []

        await self._rate_limiter.acquire()
        await self._client.connect()

        if not self._client._authorized:
            return []

        # Search for "{category} chat"
        query = f"{category} chat"
        try:
            result = await self._client.client.search_entities(query, limit=self.max_per_category)
            for entity in result:
                username = getattr(entity, "username", None)
                if username:
                    usernames.append(username)
        except FloodWaitError:
            raise
        except Exception as e:
            logger.debug("search_error", query=query, error=str(e))

        # Also search for "{category} канал" (Russian)
        query_ru = f"{category} канал"
        try:
            await self._rate_limiter.acquire()
            result = await self._client.client.search_entities(query_ru, limit=self.max_per_category)
            for entity in result:
                username = getattr(entity, "username", None)
                if username:
                    usernames.append(username)
        except FloodWaitError:
            raise
        except Exception as e:
            logger.debug("search_error", query=query_ru, error=str(e))

        return list(set(usernames))
