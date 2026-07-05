"""Application constants."""

from enum import Enum


class ChatType(str, Enum):
    """Chat type enumeration."""

    CHANNEL = "channel"
    GROUP = "group"
    SUPERGROUP = "supergroup"


class QueueStatus(str, Enum):
    """URL queue status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    VALIDATED = "validated"
    INVALID = "invalid"
    INDEXED = "indexed"
    ERROR = "error"


class CrawlAction(str, Enum):
    """Crawl action enumeration."""

    DISCOVER = "discover"
    VALIDATE = "validate"
    EXTRACT_METADATA = "extract_metadata"
    UPDATE = "update"


class CrawlStatus(str, Enum):
    """Crawl status enumeration."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


# Telegram URL patterns
TELEGRAM_URL_PATTERNS = [
    r"https?://t\.me/([a-zA-Z0-9_]{5,})",
    r"https?://telegram\.me/([a-zA-Z0-9_]{5,})",
    r"tg://resolve\?domain=([a-zA-Z0-9_]{5,})",
]

# Minimum username length
MIN_USERNAME_LENGTH = 5

# Maximum batch size
MAX_BATCH_SIZE = 100

# Default pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# FTS configuration
FTS_LANGUAGE = "simple"

# Score weights for quality calculation
QUALITY_SCORE_WEIGHTS = {
    "activity": 0.25,
    "popularity": 0.30,
    "health": 0.25,
    "growth": 0.20,
}
