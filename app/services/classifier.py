"""Chat classification service."""

import re
from collections import Counter


class Classifier:
    """Classifies chats by language and topic."""

    # Language detection patterns
    LANGUAGE_PATTERNS = {
        "ru": [
            r"[а-яА-ЯёЁ]",
            r"(?:канал|чат|группа|новости|обсуждение)",
        ],
        "en": [
            r"[a-zA-Z]",
            r"(?:channel|chat|group|news|discussion)",
        ],
        "uk": [
            r"[а-яА-ЯёЁіїєґ]",
            r"(?:канал|чат|група|новини|обговорення)",
        ],
        "es": [
            r"[áéíóúñ¿¡]",
            r"(?:canal|grupo|noticias|discusión)",
        ],
        "de": [
            r"[äöüßÄÖÜ]",
            r"(?:kanal|gruppe|nachrichten|diskussion)",
        ],
        "fr": [
            r"[àâéèêëïîôùûüÿçœæ]",
            r"(?:chaîne|groupe|actualités|discussion)",
        ],
    }

    # Topic detection keywords
    TOPIC_KEYWORDS = {
        "technology": [
            "tech", "programming", "coding", "software", "hardware",
            "python", "javascript", "ai", "ml", "crypto", "bitcoin",
            "технологии", "программирование", "код", "софт",
        ],
        "news": [
            "news", "media", "press", "daily", "breaking",
            "новости", "медиа", "пресса", "ежедневно",
        ],
        "crypto": [
            "crypto", "bitcoin", "ethereum", "trading", "defi", "nft",
            "крипто", "биткоин", "торговля", "инвестиции",
        ],
        "gaming": [
            "gaming", "games", "esport", "steam", "playstation", "xbox",
            "игры", "гейминг", "киберспорт",
        ],
        "business": [
            "business", "startup", "entrepreneur", "marketing", "sales",
            "бизнес", "стартап", "маркетинг", "продажи",
        ],
        "education": [
            "education", "learning", "course", "tutorial", "study",
            "образование", "обучение", "курс", "tutorial",
        ],
        "entertainment": [
            "fun", "humor", "meme", "joke", "movie", "music",
            "развлечение", "юмор", "мем", "фильм", "музыка",
        ],
        "science": [
            "science", "physics", "chemistry", "biology", "research",
            "наука", "физика", "химия", "биология", "исследование",
        ],
    }

    def detect_language(self, text: str) -> str | None:
        """Detect language of text."""
        if not text:
            return None

        scores = {}
        text_lower = text.lower()

        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                score += len(matches)
            scores[lang] = score

        if not scores:
            return None

        max_score = max(scores.values())
        if max_score == 0:
            return None

        # Return language with highest score
        return max(scores, key=scores.get)

    def detect_topic(self, title: str, description: str | None = None) -> str | None:
        """Detect topic of chat."""
        text = f"{title} {description or ''}".lower()

        scores = {}
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[topic] = score

        if not scores:
            return None

        return max(scores, key=scores.get)

    def classify(self, title: str, description: str | None = None) -> dict:
        """Classify chat by language and topic."""
        return {
            "language": self.detect_language(f"{title} {description or ''}"),
            "topic": self.detect_topic(title, description),
        }
