"""URL normalization service."""

import re
from urllib.parse import urlparse, parse_qs, unquote

from app.config.constants import TELEGRAM_URL_PATTERNS, MIN_USERNAME_LENGTH


class Normalizer:
    """Normalizes Telegram URLs."""

    def normalize(self, url: str) -> str | None:
        """Normalize URL and extract username."""
        url = url.strip()
        url = unquote(url)

        # Try t.me/username pattern
        for pattern in TELEGRAM_URL_PATTERNS:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                username = match.group(1)
                if len(username) >= MIN_USERNAME_LENGTH:
                    return username.lower()

        # Try tg://resolve?domain=username
        if url.startswith("tg://"):
            try:
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                if "domain" in params:
                    username = params["domain"][0]
                    if len(username) >= MIN_USERNAME_LENGTH:
                        return username.lower()
            except Exception:
                pass

        return None

    def extract_username(self, url: str) -> str | None:
        """Extract username from URL."""
        return self.normalize(url)

    def to_public_url(self, username: str) -> str:
        """Convert username to public URL."""
        return f"https://t.me/{username}"

    def is_valid_telegram_url(self, url: str) -> bool:
        """Check if URL is a valid Telegram link."""
        return self.normalize(url) is not None
