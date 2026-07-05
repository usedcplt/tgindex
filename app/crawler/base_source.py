"""Base source for URL discovery."""

from abc import ABC, abstractmethod


class BaseSource(ABC):
    """Abstract base class for discovery sources."""

    def __init__(self, name: str, config: dict | None = None) -> None:
        self.name = name
        self.config = config or {}

    @abstractmethod
    async def discover(self) -> list[str]:
        """Discover Telegram URLs.

        Returns:
            List of discovered URLs.
        """
        ...

    async def get_info(self) -> dict:
        """Get source information."""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "config": self.config,
        }
