"""Metadata extraction service."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chat_repository import ChatRepository
from app.repositories.queue_repository import QueueRepository
from app.services.classifier import Classifier
from app.services.scheduler_service import SchedulerService
from app.telegram.metadata_extractor import MetadataExtractor
from app.telegram.rate_limiter import RateLimiter

logger = structlog.get_logger()


class MetadataService:
    """Orchestrates metadata extraction and storage."""

    def __init__(
        self,
        session: AsyncSession,
        metadata_extractor: MetadataExtractor,
        rate_limiter: RateLimiter,
    ) -> None:
        self.session = session
        self.metadata_extractor = metadata_extractor
        self.rate_limiter = rate_limiter
        self.chat_repo = ChatRepository(session)
        self.queue_repo = QueueRepository(session)
        self.classifier = Classifier()
        self.scheduler_service = SchedulerService(session)

    async def extract_and_store(self, url: str) -> dict:
        """Extract metadata and store in database."""
        try:
            await self.rate_limiter.acquire()

            metadata = await self.metadata_extractor.extract(url)
            if not metadata:
                return {"success": False, "error": "Could not extract metadata"}

            classification = self.classifier.classify(
                metadata.get("title", ""),
                metadata.get("description", ""),
            )

            chat = await self.chat_repo.get_by_telegram_id(metadata["telegram_id"])
            if chat:
                await self._update_existing_chat(chat, metadata, classification)
            else:
                await self._create_new_chat(metadata, classification)

            return {"success": True, "data": metadata}

        except Exception as e:
            logger.error("metadata_extraction_failed", url=url, error=str(e))
            return {"success": False, "error": str(e)}

    async def _create_new_chat(self, metadata: dict, classification: dict) -> None:
        """Create new chat record."""
        await self.chat_repo.create(
            {
                "telegram_id": metadata["telegram_id"],
                "access_hash": metadata.get("access_hash", 0),
                "username": metadata.get("username"),
                "public_url": metadata.get("public_url"),
                "title": metadata.get("title", ""),
                "description": metadata.get("description"),
                "chat_type": metadata.get("chat_type", "channel"),
                "member_count": metadata.get("member_count", 0),
                "language": classification.get("language"),
                "topic": classification.get("topic"),
                "discovery_source": metadata.get("source"),
                "avatar_hash": metadata.get("avatar_hash"),
                "health_score": 1.0,
            }
        )

    async def _update_existing_chat(
        self, chat, metadata: dict, classification: dict
    ) -> None:
        """Update existing chat if changed."""
        changes = {}

        if metadata.get("title") and metadata["title"] != chat.title:
            changes["title"] = metadata["title"]
        if metadata.get("description") != chat.description:
            changes["description"] = metadata.get("description")
        if metadata.get("username") and metadata["username"] != chat.username:
            changes["username"] = metadata["username"]
        if metadata.get("member_count") and metadata["member_count"] != chat.member_count:
            changes["member_count"] = metadata["member_count"]
        if metadata.get("avatar_hash") and metadata["avatar_hash"] != chat.avatar_hash:
            changes["avatar_hash"] = metadata["avatar_hash"]

        if changes:
            await self.chat_repo.update(chat, changes)
