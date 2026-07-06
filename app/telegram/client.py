"""Telegram client wrapper."""

import structlog
from telethon import TelegramClient as TelethonClient
from telethon.sessions import StringSession
from telethon.errors import (
    FloodWaitError,
    UsernameNotOccupiedError,
    UsernameInvalidError,
    ChannelPrivateError,
    AuthKeyUnregisteredError,
)

from app.config import settings

logger = structlog.get_logger()


class TelegramClient:
    """Wrapper for Telethon client supporting both file and string sessions."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.client: TelethonClient | None = None
        self._authorized = False

    async def connect(self) -> None:
        """Connect to Telegram."""
        if self.client is None:
            session_string = settings.telegram.session_string

            if session_string:
                self.client = TelethonClient(
                    StringSession(session_string),
                    settings.telegram.api_id,
                    settings.telegram.api_hash,
                )
                logger.info("telegram_session_type", type="string")
            else:
                self.client = TelethonClient(
                    settings.telegram.session_name,
                    settings.telegram.api_id,
                    settings.telegram.api_hash,
                )
                logger.info("telegram_session_type", type="file")

        if not self.client.is_connected():
            await self.client.connect()
            logger.info("telegram_connected")

        if not self._authorized:
            if await self.client.is_user_authorized():
                self._authorized = True
                logger.info("telegram_authorized")
            else:
                logger.warning("telegram_not_authorized")

    async def disconnect(self) -> None:
        """Disconnect from Telegram."""
        if self.client and self.client.is_connected():
            await self.client.disconnect()

    async def check_username(self, username: str) -> dict | None:
        """Check if username exists and get basic info."""
        try:
            await self.connect()

            if not self._authorized:
                logger.error("telegram_not_authorized")
                return None

            entity = await self.client.get_entity(username)

            return {
                "telegram_id": entity.id,
                "access_hash": entity.access_hash,
                "username": getattr(entity, "username", None),
                "title": getattr(entity, "title", None) or getattr(entity, "first_name", None),
                "description": getattr(entity, "about", None),
                "chat_type": self._get_chat_type(entity),
                "member_count": getattr(entity, "participants_count", None) or 0,
            }

        except UsernameNotOccupiedError:
            logger.debug("username_not_occupied", username=username)
            return None
        except UsernameInvalidError:
            logger.debug("username_invalid", username=username)
            return None
        except ChannelPrivateError:
            logger.debug("channel_private", username=username)
            return None
        except FloodWaitError as e:
            # Don't raise - handle in validator with retry
            logger.warning("flood_wait", username=username, seconds=e.seconds)
            return None
        except AuthKeyUnregisteredError:
            logger.error("auth_key_unregistered")
            self._authorized = False
            return None
        except Exception as e:
            logger.error("check_username_failed", username=username, error=str(e))
            return None

    async def search_entities(self, query: str, limit: int = 20) -> list:
        """Search for entities by query."""
        try:
            await self.connect()

            if not self._authorized:
                return []

            result = await self.client.search_entities(query, limit=limit)
            return result

        except FloodWaitError:
            raise
        except Exception as e:
            logger.debug("search_entities_failed", query=query, error=str(e))
            return []

    def _get_chat_type(self, entity) -> str:
        """Determine chat type from entity."""
        if hasattr(entity, "megagroup") and entity.megagroup:
            return "supergroup"
        elif hasattr(entity, "broadcast") and entity.broadcast:
            return "channel"
        else:
            return "group"
