import logging
import os
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from core import config
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

user_id = int(os.getenv('USER_ID'))

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Handler untuk perintah /get_id
async def startid_command(client, message):
    global LAST_MESSAGE_ID_WITH_GET_ID_DATE
    chat_id = message.chat.id
    user_name = message.from_user.username
    logging.info(f"Menerima perintah /get_id dari {user_name}, chat_id: {chat_id}")

    button = KeyboardButton("Bagikan nomor telepon Anda", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    
    sent_message = await message.reply_text(
        'Klik tombol di bawah ini untuk membagikan nomor telepon Anda:',
        reply_markup=keyboard
    )

    # Store the last message ID
    config.LAST_MESSAGE_ID_WITH_GET_ID_DATE = sent_message.message_id
    logging.info(f"Pesan terkirim dengan ID: {sent_message.message_id}")

# Handler untuk menangani pesan kontak
async def handle_contact(client, message):
    global LAST_MESSAGE_ID_WITH_GET_ID_DATE
    logger.info("Menangani pesan kontak...")
    phone_number = message.contact.phone_number
    user_name = message.from_user.username
    user_id = message.from_user.id
    logger.info(f"Menerima kontak dari {user_name}, nomor telepon: {phone_number}")

    group_message = (
        f"Informasi pengguna:\n"
        f"Username: {user_name}\n"
        f"User ID: {user_id}\n"
        f"Nomor Telepon: {phone_number}"
    )

    if config.LAST_MESSAGE_ID_WITH_GET_ID_DATE:
        await client.send_message(
            chat_id=config.DISCUSS_GROUP,
            text=group_message,
            reply_to_message_id=config.LAST_MESSAGE_ID_WITH_GET_ID_DATE
        )
        logging.info(f"Pesan dikirim ke grup dengan reply_to_message_id: {config.LAST_MESSAGE_ID_WITH_GET_ID_DATE}")
    else:
        await client.send_message(
            chat_id=config.DISCUSS_GROUP,
            text=group_message
        )
        user_id = int(os.getenv('USER_ID'))
        await client.send_message(
            chat_id=user_id,
            text="Tidak ada ID pesan yang tersimpan di dalam grup"
        )
        logging.info("Tidak ada ID pesan yang tersimpan di dalam grup")

    await message.reply_text(
        f'Terima kasih, berikut adalah data akun telegram Anda:\n'
        f'Username: {user_name}\n'
        f'User ID: {user_id}\n'
        f'Nomor Telepon: {phone_number}',
        reply_markup=ReplyKeyboardRemove()
    )
