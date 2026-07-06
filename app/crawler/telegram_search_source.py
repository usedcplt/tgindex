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

    # Top categories - high quality, focused
    CATEGORIES = [
        # EN
        "crypto", "bitcoin", "ethereum", "nft", "trading",
        "python", "javascript", "programming", "developer",
        "gaming", "games", "esport",
        "news", "media",
        "business", "startup", "marketing",
        "tech", "ai", "machine learning",
        "music", "movies", "anime",
        "sports", "football", "basketball",
        "education", "learning",
        "travel", "tourism",
        "food", "cooking",
        "health", "fitness",
        "fashion", "beauty",
        "art", "design",
        "science",
        "cars", "auto",
        "jobs", "freelance",
        "english", "languages",
        "books", "reading",
        "linux", "windows",
        "android", "ios",
        "web", "frontend", "backend",
        "database", "sql",
        "devops", "docker",
        "cybersecurity", "hacking",
        "crypto", "blockchain", "web3",
        "investing", "stocks",
        "realestate",
        "parenting", "family",
        "pets", "dogs",
        "gardening", "plants",
        "diy", "crafts",
        "podcast", "youtube",
        "writing", "blogging",
        "yoga", "meditation",
        "philosophy", "psychology",
        "history",
        "astronomy", "space",
        "mathematics",
        "economics", "finance",
        "dating", "relationships",
        "watches",
        "tech", "gadgets",
        "smartphones", "laptops",
        "esports", "streaming",
        "content creation",
        "social media", "instagram", "tiktok",
        "dating",
        "travel", "backpacking",
        "remote work",
        "freelancing",
        "startup", "entrepreneur",
        "marketing",
        "seo",
        "ecommerce",
        "crypto",
        "investing",
        "real estate",
        "personal finance",
        "taxes",
        "legal",
        "health", "wellness",
        "nutrition",
        "sleep",
        "productivity",
        "minimalism",
        "sustainability",
        "vegan",
        "keto",
        "running", "marathon",
        "cycling", "swimming",
        "yoga",
        "martial arts",
        "weightlifting",
        "hiking",
        "camping",
        "fishing",
        "cooking", "baking",
        "cocktails",
        "coffee", "tea",
        "wine", "beer",
        "sushi",
        "vegan recipes",
        "meal prep",
        "gardening",
        "indoor plants",
        "pets", "dog training",
        "diy", "woodworking",
        "3d printing",
        "robotics", "electronics",
        "photography",
        "videography",
        "youtube",
        "podcasting",
        "music production",
        "guitar", "piano",
        "singing",
        "writing",
        "self improvement",
        "productivity",
        "meditation",
        "stoicism",
        "languages",
        "history",
        "astronomy",
        "paranormal",
        "true crime",
        "comedy",
        "horror",
        "fantasy",
        "manga",
        "anime",
        "movies", "film",
        "tv shows", "netflix",
        "music", "concerts",
        "sports", "nba",
        "soccer",
        "tennis",
        "f1",
        "mma", "ufc",
        "esports", "league of legends",
        "minecraft",
        "chess",
        "board games",
        "cosplay",
        "fashion", "streetwear",
        "sneakers",
        "watches",
        "cars", "supercars",
        "motorcycles",
        "aviation",
        "sailing",
        "diving",
        "skiing",
        "surfing",
        "rock climbing",
        "hiking",
        "camping",
        "digital nomad",
        "freelancing",
        "entrepreneurship",
        "marketing",
        "seo",
        "ecommerce",
        "crypto",
        "investing",
        "real estate",
        "personal finance",
        "education",
        "coding bootcamps",
        "job hunting",
        "career growth",
        "productivity",
        "ai tools", "chatgpt",
        "cybersecurity",
        "linux",
        "windows",
        "android", "ios",
        "web development",
        "nodejs", "django",
        "databases", "sql",
        "cloud", "aws",
        "devops",
        "machine learning",
        "data science",
        "robotics",
        "blockchain",
        "vr", "ar",
        "quantum computing",
        "space", "nasa",
        "climate",
        "renewable energy",
        "biotech",
        "agriculture",
        "health tech",
        "fintech",
        "edtech",
        "cleantech",
        "developer tools",
        "monitoring",
        "ci/cd",
        "security",
        "cloud",
        "ai tools",
        "productivity tools",
        # RU
        "программирование", "разработка",
        "игры", "гейминг",
        "новости", "медиа",
        "бизнес", "стартап",
        "технологии", "айти",
        "музыка", "фильмы", "аниме",
        "спорт", "футбол",
        "образование",
        "путешествия",
        "еда", "кулинария",
        "здоровье", "фитнес",
        "мода",
        "искусство", "дизайн",
        "наука",
        "автомобили",
        "вакансии", "фриланс",
        "языки",
        "книги",
        "linux", "windows",
        "android", "ios",
        "веб", "фронтенд",
        "базы данных", "sql",
        "девопс", "docker",
        "крипто", "трейдинг",
        "инвестиции",
        "недвижимость",
        "психология",
        "медитация",
        "йога",
        "шахматы",
        "ютуб",
        "соцсети",
        "путешествия",
        "удалённая работа",
        "стартап",
        "маркетинг",
        "крипто",
        "инвестиции",
        "личные финансы",
        "здоровье",
        "продуктивность",
        "саморазвитие",
    ]

    def __init__(
        self,
        name: str = "telegram_search",
        config: dict | None = None,
    ) -> None:
        super().__init__(name, config)
        cfg = config or {}
        self.categories = cfg.get("categories", self.CATEGORIES)
        self.max_per_category = cfg.get("max_per_category", 10)
        self._client: TelegramClient | None = None
        self._rate_limiter: RateLimiter | None = None

    async def discover(self) -> list[str]:
        """Discover Telegram chats using search."""
        if self._client is None:
            self._client = TelegramClient()
        if self._rate_limiter is None:
            self._rate_limiter = RateLimiter()

        all_usernames = []

        for category in self.categories:
            try:
                usernames = await self._search_category(category)
                all_usernames.extend(usernames)
            except FloodWaitError as e:
                logger.warning("flood_wait", category=category, seconds=e.seconds)
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logger.debug("category_failed", category=category, error=str(e))

            await asyncio.sleep(0.3)

        urls = [f"https://t.me/{username}" for username in all_usernames if username]
        unique_urls = list(set(urls))

        logger.info("telegram_search_completed", categories=len(self.categories), found=len(unique_urls))
        return unique_urls

    async def _search_category(self, category: str) -> list[str]:
        """Search for chats in a category."""
        usernames = []

        await self._rate_limiter.acquire()
        await self._client.connect()

        if not self._client._authorized:
            return []

        query = f"{category} chat"
        try:
            result = await self._client.search_entities(query, limit=self.max_per_category)
            for entity in result:
                username = getattr(entity, "username", None)
                if username:
                    usernames.append(username)
        except FloodWaitError:
            raise
        except Exception as e:
            logger.debug("search_error", query=query, error=str(e))

        return list(set(usernames))
