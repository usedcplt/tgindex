"""Deduplication service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.queue_repository import QueueRepository
from app.utils.hash_utils import compute_url_hash


class Deduplicator:
    """Deduplication service for URL queue."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.queue_repo = QueueRepository(session)

    async def is_duplicate(self, url: str) -> bool:
        """Check if URL is a duplicate."""
        url_hash = compute_url_hash(url)
        return await self.queue_repo.exists_by_url_hash(url_hash)

    async def add_to_queue(
        self,
        url: str,
        normalized_url: str,
        source: str | None = None,
        priority: int = 0,
    ) -> bool:
        """Add URL to queue if not duplicate. Returns True if added."""
        url_hash = compute_url_hash(normalized_url)

        if await self.queue_repo.exists_by_url_hash(url_hash):
            return False

        await self.queue_repo.create(
            {
                "url": url,
                "normalized_url": normalized_url,
                "url_hash": url_hash,
                "source": source,
                "priority": priority,
                "status": "pending",
            }
        )
        return True

    async def add_batch(
        self,
        urls: list[dict],
        source: str | None = None,
    ) -> int:
        """Add batch of URLs to queue using bulk insert. Returns count of new URLs added."""
        if not urls:
            return 0

        # Prepare items with hashes
        items = []
        for item in urls:
            url = item.get("url", "")
            normalized_url = item.get("normalized_url", url)
            priority = item.get("priority", 0)
            url_hash = compute_url_hash(normalized_url)

            items.append({
                "url": url,
                "normalized_url": normalized_url,
                "url_hash": url_hash,
                "source": source,
                "priority": priority,
                "status": "pending",
            })

        # Bulk insert (skips duplicates automatically)
        inserted = await self.queue_repo.bulk_insert(items)
        return inserted
