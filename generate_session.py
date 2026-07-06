"""Generate Telegram session string for Render deployment.

Run this LOCALLY (not on Render) to get your session string.
Then add it to Render environment variables.
"""
import asyncio
import sys
import os
from telethon import TelegramClient
from telethon.sessions import StringSession


async def main():
    print("=" * 60)
    print("TGIndex - Session String Generator")
    print("=" * 60)
    print()
    print("This script will authorize your Telegram account")
    print("and generate a session string for Render deployment.")
    print()

    api_id = int(input("Enter your Telegram API ID: "))
    api_hash = input("Enter your Telegram API hash: ")

    # Remove existing session file if exists
    session_file = "tgindex_session.session"
    if os.path.exists(session_file):
        os.remove(session_file)
        print(f"Removed existing session file: {session_file}")

    # Create fresh client with StringSession
    client = TelegramClient(StringSession(), api_id, api_hash)

    print()
    print("Connecting to Telegram...")
    print("You will be asked for your phone number and code.")
    print()

    await client.start()

    # Get the session string
    session_string = client.session.save()

    if not session_string:
        print()
        print("ERROR: Could not generate session string.")
        print("Make sure you completed the authorization.")
        await client.disconnect()
        sys.exit(1)

    print()
    print("=" * 60)
    print("SUCCESS! Your session string:")
    print("=" * 60)
    print()
    print(session_string)
    print()
    print("=" * 60)
    print("Copy the ENTIRE string above")
    print("and add it to Render as TELEGRAM_SESSION_STRING")
    print("=" * 60)

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
