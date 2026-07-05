"""Update worker for refreshing existing chat metadata."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chat_repository import ChatRepository
from app.services.scheduler_service import SchedulerService
from app.telegram.client import TelegramClient
from app.telegram.metadata_extractor import MetadataExtractor
from app.telegram.rate_limiter import RateLimiter

logger = structlog.get_logger()


class UpdateWorker:
    """Worker for updating existing chat metadata."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.chat_repo = ChatRepository(session)
        self.telegram_client = TelegramClient()
        self.metadata_extractor = MetadataExtractor()
        self.rate_limiter = RateLimiter()
        self.scheduler_service = SchedulerService(session)

    async def run(self) -> dict:
        """Run update on chats due for checking."""
        logger.info("update_worker_started")

        try:
            chats = await self.scheduler_service.get_chats_due_for_check(limit=50)

            if not chats:
                logger.info("no_chats_due_for_check")
                return {"processed": 0}

            updated_count = 0
            error_count = 0

            for chat in chats:
                try:
                    await self.rate_limiter.acquire()

                    metadata = await self.metadata_extractor.extract_by_id(
                        chat.telegram_id, chat.access_hash
                    )

                    if metadata:
                        changes = self._detect_changes(chat, metadata)
                        if changes:
                            await self.chat_repo.update(chat, changes)
                            updated_count += 1

                    await self.scheduler_service.schedule_check(chat.id)

                except Exception as e:
                    logger.error("chat_update_failed", chat_id=chat.id, error=str(e))
                    error_count += 1

            logger.info(
                "update_worker_completed",
                total=len(chats),
                updated=updated_count,
                errors=error_count,
            )

            return {
                "processed": len(chats),
                "updated": updated_count,
                "errors": error_count,
            }

        except Exception as e:
            logger.error("update_worker_failed", error=str(e))
            raise

    def _detect_changes(self, chat, metadata: dict) -> dict:
        """Detect changes between existing and new metadata."""
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

        return changes
