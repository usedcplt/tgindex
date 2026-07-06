"""Queue repository for URL processing."""

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.url_queue import UrlQueue

from .base import BaseRepository


class QueueRepository(BaseRepository[UrlQueue]):
    """Queue repository with batch operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UrlQueue)

    async def get_by_url_hash(self, url_hash: str) -> UrlQueue | None:
        """Get queue item by URL hash."""
        result = await self.session.execute(
            select(UrlQueue).where(UrlQueue.url_hash == url_hash)
        )
        return result.scalar_one_or_none()

    async def exists_by_url_hash(self, url_hash: str) -> bool:
        """Check if URL hash exists in queue."""
        result = await self.session.execute(
            select(func.count()).where(UrlQueue.url_hash == url_hash)
        )
        return result.scalar_one() > 0

    async def batch_exists_by_url_hash(self, url_hashes: list[str]) -> set[str]:
        """Check which URL hashes exist in queue. Returns set of existing hashes."""
        if not url_hashes:
            return set()

        result = await self.session.execute(
            select(UrlQueue.url_hash).where(UrlQueue.url_hash.in_(url_hashes))
        )
        return set(result.scalars().all())

    async def bulk_insert(self, items: list[dict]) -> int:
        """Bulk insert new queue items, skipping duplicates. Returns count of inserted."""
        if not items:
            return 0

        stmt = pg_insert(UrlQueue).values(items)
        stmt = stmt.on_conflict_do_nothing(index_elements=["url_hash"])
        result = await self.session.execute(stmt)
        return result.rowcount

    async def get_pending_batch(self, batch_size: int = 50) -> list[UrlQueue]:
        """Get pending URLs for processing."""
        result = await self.session.execute(
            select(UrlQueue)
            .where(UrlQueue.status == "pending")
            .order_by(UrlQueue.priority.desc(), UrlQueue.created_at.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        return list(result.scalars().all())

    async def get_validated_batch(self, batch_size: int = 50) -> list[UrlQueue]:
        """Get validated URLs for metadata extraction."""
        result = await self.session.execute(
            select(UrlQueue)
            .where(UrlQueue.status == "validated")
            .order_by(UrlQueue.created_at.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        return list(result.scalars().all())

    async def mark_processing(self, ids: list[int]) -> None:
        """Mark URLs as processing."""
        await self.session.execute(
            update(UrlQueue)
            .where(UrlQueue.id.in_(ids))
            .values(status="processing", updated_at=datetime.utcnow())
        )

    async def mark_validated(self, ids: list[int]) -> None:
        """Mark URLs as validated."""
        await self.session.execute(
            update(UrlQueue)
            .where(UrlQueue.id.in_(ids))
            .values(
                status="validated",
                processed_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

    async def mark_invalid(self, ids: list[int], error_message: str | None = None) -> None:
        """Mark URLs as invalid."""
        await self.session.execute(
            update(UrlQueue)
            .where(UrlQueue.id.in_(ids))
            .values(
                status="invalid",
                error_message=error_message,
                processed_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

    async def mark_indexed(self, ids: list[int]) -> None:
        """Mark URLs as indexed."""
        await self.session.execute(
            update(UrlQueue)
            .where(UrlQueue.id.in_(ids))
            .values(
                status="indexed",
                processed_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

    async def mark_error(self, ids: list[int], error_message: str) -> None:
        """Mark URLs as error."""
        await self.session.execute(
            update(UrlQueue)
            .where(UrlQueue.id.in_(ids))
            .values(
                status="error",
                error_message=error_message,
                attempts=UrlQueue.attempts + 1,
                updated_at=datetime.utcnow(),
            )
        )

    async def retry_errors(self, max_retries: int = 3, batch_size: int = 100) -> int:
        """Retry error URLs that haven't exceeded max retries."""
        result = await self.session.execute(
            select(UrlQueue.id)
            .where(UrlQueue.status == "error")
            .where(UrlQueue.attempts < max_retries)
            .limit(batch_size)
        )
        ids = [row[0] for row in result.all()]

        if ids:
            await self.session.execute(
                update(UrlQueue)
                .where(UrlQueue.id.in_(ids))
                .values(
                    status="pending",
                    error_message=None,
                    updated_at=datetime.utcnow(),
                )
            )

        return len(ids)

    async def reset_stuck_processing(self, timeout_minutes: int = 10) -> int:
        """Reset URLs stuck in 'processing' status."""
        cutoff = datetime.utcnow() - __import__("datetime").timedelta(minutes=timeout_minutes)
        result = await self.session.execute(
            select(UrlQueue.id)
            .where(UrlQueue.status == "processing")
            .where(UrlQueue.updated_at < cutoff)
            .limit(100)
        )
        ids = [row[0] for row in result.all()]

        if ids:
            await self.session.execute(
                update(UrlQueue)
                .where(UrlQueue.id.in_(ids))
                .values(
                    status="pending",
                    updated_at=datetime.utcnow(),
                )
            )

        return len(ids)

    async def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        result = await self.session.execute(
            select(
                UrlQueue.status,
                func.count(UrlQueue.id),
            ).group_by(UrlQueue.status)
        )
        stats = {row[0]: row[1] for row in result.all()}

        return {
            "pending": stats.get("pending", 0),
            "processing": stats.get("processing", 0),
            "validated": stats.get("validated", 0),
            "invalid": stats.get("invalid", 0),
            "indexed": stats.get("indexed", 0),
            "error": stats.get("error", 0),
            "total": sum(stats.values()),
        }

    async def cleanup_old_entries(self, days: int = 30) -> int:
        """Clean up old processed entries."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)

        from sqlalchemy import delete
        result = await self.session.execute(
            delete(UrlQueue).where(
                UrlQueue.status.in_(["indexed", "invalid"]),
                UrlQueue.processed_at < cutoff,
            )
        )

        return result.rowcount
