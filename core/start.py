import logging
import os
from pyrogram import Client, filters
from core import config

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

AVAILABLE_COMMANDS = [
    '/start - Untuk Menampilkan Command Perintah',
    '/get_id - Untuk Mengambil chat ID Dan Nomor Telepon',
    '/getgroupid - Untuk Mendapatkan ID Grup'
]

def schedule_messages(app: Client):
    config.schedule_daily_message(app)

async def start_command(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username or "No username"
    user_data = f"User ID: {user_id}\nName: {first_name}\nUsername: {username}"
    
    if config.LAST_MESSAGE_ID_WITH_DATE:
        await client.send_message(
            config.DISCUSS_GROUP,
            f"New User Data:\n{user_data}",
            reply_to_message_id=config.LAST_MESSAGE_ID_WITH_DATE
        )
        logging.info(f"Pesan baru dikirim dengan reply_to_message_id: {config.LAST_MESSAGE_ID_WITH_DATE}")
    else:
        await client.send_message(
            config.DISCUSS_GROUP,
            f"New User Data:\n{user_data}"
        )
        predefined_user_id = int(os.getenv('USER_ID'))
        await client.send_message(
            predefined_user_id,
            "Tidak ada ID pesan yang tersimpan didalam grup"
        )
        logging.info("Tidak ada ID pesan yang tersimpan di dalam grup")

    
    command_list = '\n'.join(AVAILABLE_COMMANDS)
    await message.reply_text(f'Selamat datang! Berikut daftar perintah yang tersedia:\n{command_list}')

