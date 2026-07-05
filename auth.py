"""Telegram authorization script."""
import asyncio
from telethon import TelegramClient
from app.config import settings


async def main():
    client = TelegramClient(
        settings.telegram.session_name,
        settings.telegram.api_id,
        settings.telegram.api_hash,
    )
    await client.start()
    print("Авторизация успешна!")
    me = await client.get_me()
    print(f"Вы вошли как: {me.first_name}")
    await client.disconnect()


asyncio.run(main())
