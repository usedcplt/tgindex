"""URL parsing and normalization utilities."""

import re
from urllib.parse import urlparse, parse_qs, unquote

from app.config.constants import TELEGRAM_URL_PATTERNS, MIN_USERNAME_LENGTH


def normalize_url(url: str) -> str:
    """Normalize Telegram URL."""
    url = url.strip()
    url = unquote(url)

    # Convert t.me links
    if "t.me/" in url or "telegram.me/" in url:
        username = extract_username(url)
        if username:
            return f"https://t.me/{username}"

    # Convert tg:// links
    if url.startswith("tg://"):
        username = extract_username_from_tg(url)
        if username:
            return f"https://t.me/{username}"

    return url


def extract_username(url: str) -> str | None:
    """Extract username from Telegram URL."""
    for pattern in TELEGRAM_URL_PATTERNS:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            username = match.group(1)
            if len(username) >= MIN_USERNAME_LENGTH:
                return username.lower()
    return None


def extract_username_from_tg(url: str) -> str | None:
    """Extract username from tg:// URL."""
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


def parse_telegram_url(url: str) -> dict | None:
    """Parse Telegram URL and extract components."""
    username = extract_username(url)
    if not username:
        return None

    return {
        "username": username,
        "public_url": f"https://t.me/{username}",
        "normalized_url": f"https://t.me/{username}",
    }


def is_telegram_url(url: str) -> bool:
    """Check if URL is a Telegram link."""
    return any(
        re.search(pattern, url, re.IGNORECASE)
        for pattern in TELEGRAM_URL_PATTERNS
    )


def extract_telegram_links(text: str) -> list[str]:
    """Extract all Telegram links from text."""
    links = []
    for pattern in TELEGRAM_URL_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) >= MIN_USERNAME_LENGTH:
                links.append(f"https://t.me/{match.lower()}")
    return list(set(links))
