import logging
import os
from pyrogram import Client, filters
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')
TOKEN_BOT_UTAMA = os.getenv('TOKEN_BOT_UTAMA')

# Initialize the bot client with session in 'sessions' folder
app = Client(
    "pyrogram_session",  
    api_id=api_id,
    api_hash=api_hash,
    bot_token=TOKEN_BOT_UTAMA,
    workdir="sessions"  
)

# Group chat ID and message ID to reply to
GROUP_CHAT_ID = -1002221625169
REPLY_TO_MESSAGE_ID = 293

# Whitelist of user IDs
DEV_MODE_ALLOWED = [
    6320998144,  # ID user monarchiv
    1238655724,  # ID user XylenceOMX
    7180227348,  # ID User XylenceXY
    0,  # 
    # Add other user IDs here
]

# Check if user is whitelisted
def is_user_whitelisted(user_id):
    return user_id in DEV_MODE_ALLOWED

# Handler to capture and forward voice notes
@app.on_message(filters.voice)
async def capture_and_forward_voice(client, message):
    if is_user_whitelisted(message.from_user.id):
        logging.info(f"Pesan suara diterima dengan ID: {message.id} di chat {message.chat.id}")

        # Unduh pesan suara
        file_path = await client.download_media(message.voice.file_id)

        # Kirim pesan suara ke grup yang ditentukan dan balas ke ID pesan tertentu
        await client.send_voice(
            chat_id=GROUP_CHAT_ID,
            voice=file_path,
            reply_to_message_id=REPLY_TO_MESSAGE_ID
        )
        logging.info(f"Pesan suara diteruskan ke grup {GROUP_CHAT_ID} dengan reply_to_message_id: {REPLY_TO_MESSAGE_ID}")

        # Balas ke pesan asli dengan pesan sukses
        await message.reply_text("Voice Note Berhasil Diteruskan")
    else:
        await message.reply_text("Anda tidak diizinkan menggunakan bot ini")
        logging.info(f"Pesan suara dari user non-whitelist {message.from_user.id} ditolak")

# Handler to log message IDs and content
@app.on_message()
async def log_message_id(client, message):
    message_content = message.text if message.text else "Pesan non-teks"
    logging.info(f"Pesan diterima dengan ID: {message.id} di chat {message.chat.id}")
    logging.info(f"Konten pesan: {message_content}")

# Jalankan klien Pyrogram
if __name__ == '__main__':
    app.run()
