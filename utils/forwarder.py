import csv
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use the same variable names as in your .env file
TOKEN_BOT_UTAMA = os.getenv('TOKEN_BOT_UTAMA')
ID_AKUN_UTAMA = os.getenv('USERNAME_MAIN_ACCOUNT')
GROUP_ID = int(os.getenv('GROUP_ID'))
api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')
phone = os.getenv('phone')
SESSIONS_FOLDER = 'sessions'

# Check if required environment variables are set
if not api_id or not api_hash or not TOKEN_BOT_UTAMA:
    raise ValueError("API_ID, API_HASH, and TOKEN_BOT_UTAMA must be set in the .env file.")

async def forward_all_with_link(csv_file_path, message_text):
    app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=TOKEN_BOT_UTAMA)
    await app.start()

    # Mendeteksi dan memisahkan perintah dari teks
    if " " in message_text:
        command, message_text = message_text.split(' ', 1)
    else:
        command = message_text
        message_text = ""

    url_pattern = re.compile(r'https?://[^\s]+')
    urls = url_pattern.findall(message_text)
    if urls:
        # Ambil URL pertama saja untuk contoh ini
        url = urls[0]
        # Hapus URL dari teks pesan
        message_text = url_pattern.sub("", message_text).strip()
        # Buat tombol inline
        button = InlineKeyboardMarkup([[InlineKeyboardButton("Open Link", url=url)]])

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            user_id = int(row['ID']) if row['ID'] else None
            username = row['Username'] if row['Username'] else None
            try:
                if user_id:
                    await app.send_message(user_id, message_text, reply_markup=button if urls else None)
                elif username:
                    await app.send_message(username, message_text, reply_markup=button if urls else None)
            except Exception as e:
                print(f"Failed to send message to {username or user_id} with error: {e}")

    await app.stop()
