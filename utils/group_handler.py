import os
import logging
from dotenv import load_dotenv
from pyrogram.enums import ChatType
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

GROUP_TARGET = int(os.getenv('GROUP_TARGET'))

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def get_group_id(client, message, forward_to_user_id):
    chat_id = message.chat.id
    group_id = message.chat.id
    chat_type = message.chat.type
    chat_title = message.chat.title if message.chat.title else "Unknown"

    logger.info(f"Perintah /getgroupid diterima dari chat dengan ID: {chat_id} dan tipe: {chat_type}")

    if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        # Menghapus -100 dari ID grup jika perintah digunakan di grup atau supergroup
        group_id = str(chat_id).replace('-100', '')
        await message.reply_text(f'Group ID: {group_id}\nChat ID grup ini adalah: {chat_id}')
        logger.info(f'Menerima perintah /getgroupid dari grup dengan Group ID: {group_id}, Chat ID: {chat_id}')
    elif chat_type == ChatType.CHANNEL:
        # Jika perintah digunakan di channel, tidak menghapus -100 dan meneruskan ke user ID tertentu
        logger.info(f'Menerima perintah /getgroupid dari channel dengan Channel ID: {chat_id}')
        
        # Meneruskan pesan ke user ID tertentu
        await client.send_message(
            chat_id=forward_to_user_id,
            text=f'Channel Name: {chat_title}\nChannel ID: {chat_id}'
        )
    else:
        await message.reply_text("Fitur hanya dapat digunakan di dalam grup atau channel.")
        logger.info("Perintah /getgroupid digunakan di chat yang tidak didukung.")


# Handler untuk forward message ke grup
async def forward_message_command(client: Client, message):
    try:
        # Extract link from the forwarded message
        forwarded_link = message.text.split(' ', 1)[1].strip()

        # Create inline keyboard with the forwarded link and an additional link
        inline_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Ini linknya", url=forwarded_link)],
            [InlineKeyboardButton("Verifikasi Dirimu", url="https://t.me/XylenceSec_bot?start=initial_message")]
        ])

        # Send message with inline keyboard to the group
        await client.send_message(GROUP_TARGET, "Link yang diteruskan:", reply_markup=inline_keyboard)
        logger.info(f"Link forwarded from {message.from_user.username} to group {GROUP_TARGET}.")
        await message.reply_text("Link Anda telah diteruskan ke grup.")
    except IndexError:
        await message.reply_text("Format pesan tidak sesuai. Pastikan Anda menyertakan link yang ingin diteruskan.")
    except Exception as e:
        logger.error(f"Error forwarding link: {str(e)}")
        await message.reply_text(f"Gagal meneruskan link. Error: {str(e)}")
