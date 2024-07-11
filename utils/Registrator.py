import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')

# Check if API_ID and API_HASH are set
if not api_id or not api_hash:
    raise ValueError("API_ID and API_HASH not found in environment variables.")

SESSIONS_FOLDER = 'sessions'

# Ensure the sessions folder exists
os.makedirs(SESSIONS_FOLDER, exist_ok=True)

# Register sessions function
async def register_sessions():
    # Ask user for session name
    session_name = input('\nEnter the session name (press Enter to exit): ').strip()

    if not session_name:
        return None

    # Path to save session file
    session_path = os.path.join(SESSIONS_FOLDER, session_name)

    # Create TelegramClient with the provided session name and save session file
    client = TelegramClient(
        session_path,
        api_id,
        api_hash
    )

    async with client:
        await client.start()
        me = await client.get_me()
        print(f"Session added successfully: @{me.username} | {me.first_name} {me.last_name}")

if __name__ == "__main__":
    asyncio.run(register_sessions())
