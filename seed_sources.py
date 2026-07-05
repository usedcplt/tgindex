"""Seed default discovery sources."""
import asyncio
from datetime import timedelta

from sqlalchemy import select

from app.database.engine import session_factory
from app.models.source import DiscoverySource


async def seed():
    sources = [
        {
            "name": "search_engine",
            "source_type": "search_engine",
            "is_enabled": True,
            "run_interval": timedelta(minutes=30),
            "config": {
                "queries": [
                    "telegram channel",
                    "telegram group",
                    "t.me",
                    "telegram chat invite",
                    "telegram community",
                ]
            },
        },
        {
            "name": "catalog",
            "source_type": "catalog",
            "is_enabled": True,
            "run_interval": timedelta(minutes=30),
            "config": {
                "urls": [
                    "https://t.me/s/channels",
                    "https://t.me/s/chat",
                    "https://t.me/s/groups",
                    "https://t.me/s/newchannels",
                    "https://t.me/s/BestChannelsInTelegram",
                    "https://t.me/s/russian_telegram",
                    "https://t.me/s/telegram_channels",
                    "https://t.me/s/topchannels",
                ]
            },
        },
        {
            "name": "github",
            "source_type": "github",
            "is_enabled": True,
            "run_interval": timedelta(hours=6),
            "config": {
                "queries": ["telegram channel", "t.me"],
            },
        },
        {
            "name": "recursive",
            "source_type": "recursive",
            "is_enabled": True,
            "run_interval": timedelta(minutes=30),
            "config": {"max_chats": 1000},
        },
    ]

    async with session_factory() as session:
        for source_data in sources:
            existing = await session.execute(
                select(DiscoverySource).where(
                    DiscoverySource.name == source_data["name"]
                )
            )
            if not existing.scalar_one_or_none():
                source = DiscoverySource(**source_data)
                session.add(source)
                print(f"Created source: {source_data['name']}")
            else:
                # Update existing source
                source = existing.scalar_one_or_none()
                source.config = source_data["config"]
                source.run_interval = source_data["run_interval"]
                source.is_enabled = source_data["is_enabled"]
                print(f"Updated source: {source_data['name']}")

        await session.commit()
    print("Done!")


asyncio.run(seed())
