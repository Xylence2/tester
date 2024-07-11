import os
import logging
import threading
from core import config
from pyrogram import Client, filters
from utils import scrapping
from utils.group_handler import get_group_id
from utils.get_id import startid_command, handle_contact
from utils.scrapping import handle_continue_choice
from utils.forwarder import forward_all_with_link
from utils.group_handler import forward_message_command
from utils.adder import adder_group, select_session, select_group, select_mode, unlock_database, handle_uploaded_file, cancel, cancel_addition, upload_csv, use_base_csv
from dotenv import load_dotenv
from core import config, start
from core.mode_handler import is_command_allowed, set_dev_mode
from core.voice_note import app as voice_note_app

# Load environment variables from .env file
load_dotenv()

# Use the same variable names as in your JSON file
TOKEN_BOT_UTAMA = os.getenv('TOKEN_BOT_UTAMA')
ID_AKUN_UTAMA = os.getenv('USERNAME_MAIN_ACCOUNT')
GROUP_ID = int(os.getenv('GROUP_ID'))
user_id = int(os.getenv('USER_ID'))
api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')
phone = os.getenv('phone')

# Daftar user ID yang di-whitelist
DEV_MODE_ALLOWED = [
    6320998144,  # ID user monarchiv
    1238655724,  # ID user XylenceOMX
    7180227348,  # ID User XylenceXY
    0,  # 
    # Tambahkan user ID lainnya di bawah ini
]

SESSIONS_FOLDER = 'sessions'
LAST_MESSAGE_ID_WITH_DATE = None
LAST_MESSAGE_ID_WITH_GET_ID_DATE = None
CHANNEL_ID = -1002169168287
DISCUSS_GROUP = -1002201121650

date_pattern = r'\b(?:\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{4})\b'

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize the bot client with session in 'sessions' folder
app = Client(
    "pyrogram_session",  
    api_id=api_id,
    api_hash=api_hash,
    bot_token=TOKEN_BOT_UTAMA,
    workdir="sessions"  
)

# Handler for contact messages
@app.on_message(filters.contact)
async def handle_contact_handler(client, message):
    await handle_contact(client, message)

# Handler for messages in DISCUSS_GROUP
@app.on_message(filters.chat(DISCUSS_GROUP))
async def handle_message_handler(client, message):
    await config.handle_message(client, message)

# Handler for /start command
@app.on_message(filters.command("start") & filters.create(lambda _, __, msg: is_command_allowed("/start")))
async def start_command_handler(client, message):
    await start.start_command(client, message)

# Handler for /get_id command
@app.on_message(filters.command("get_id") & filters.create(lambda _, __, msg: is_command_allowed("/get_id")))
async def startid_command_handler(client, message):
    await startid_command(client, message)

# Handler for /getgroupid command
@app.on_message(filters.command("getgroupid") & filters.create(lambda _, __, msg: is_command_allowed("/getgroupid")))
async def get_group_id_handler(client, message):
    await get_group_id(client, message, user_id)

# Handler for /forward command
@app.on_message(filters.command("forward") & filters.create(lambda _, __, msg: is_command_allowed("/forward")))
async def forward_command(client, message):
    await forward_message_command(client, message)

# Handler for /createsession command
@app.on_message(filters.command("createsession") & filters.create(lambda _, __, msg: is_command_allowed("/createsession")))
async def create_session_command(client, message):
    from utils.Registrator import register_sessions
    
    try:
        await register_sessions()
        await message.reply_text("Sesi baru berhasil ditambahkan.")
    except Exception as e:
        logger.error(f"Error saat membuat sesi: {str(e)}")
        await message.reply_text(f"Gagal menambahkan sesi baru. Error: {str(e)}")
        
# Handler for /scr_group command
@app.on_message(filters.command("scr_group") & filters.create(lambda _, __, msg: is_command_allowed("/scr_group")))
async def set_group_command(client, message):
    await scrapping.set_group_command(client, message)

# Handler for /adder_group command
@app.on_message(filters.command("adder_group") & filters.create(lambda _, __, msg: is_command_allowed("/adder_group")))
async def adder_group_command(client, message):
    await adder_group(client, message)

# Handler for /forward_all command
@app.on_message(filters.command("forward_all") & filters.create(lambda _, __, msg: is_command_allowed("/forward_all")))
async def handle_forward_all_with_link(client, message):
    json_path = "API_INFO.json"
    csv_path = "group_members.csv"
    await forward_all_with_link(json_path, csv_path, message.text)

@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    if callback_query.data.startswith('session_') or callback_query.data.startswith('group_') or callback_query.data.startswith('mode_') or callback_query.data in ["upload_csv", "use_base_csv", "cancel", "cancel_addition", "unlock_database"]:
        await handle_adder_callback(client, callback_query)
    else:
        await scrapping.handle_callback_query(client, callback_query)

# Handler for callback query ya_scrapping
@app.on_callback_query(filters.regex('^ya_scrapping$'))
async def handle_yes_scrapping(client, callback_query):
    global selected_session  # Ensure selected_session is defined in main.py
    await scrapping.handle_yes_scrapping(client, callback_query, selected_session)

# Handler for callback query tidak_scrapping
@app.on_callback_query(filters.regex('^tidak_scrapping$'))
async def handle_no_scrapping(client, callback_query):
    await scrapping.handle_no_scrapping(client, callback_query)

# Handler untuk menerima callback dari tombol inline
@app.on_callback_query()
async def callback_handler(client, callback_query):
    if callback_query.data in ["continue_scrapping", "stop_scrapping"]:
        await handle_continue_choice(client, callback_query)

# Handler for /dev_mode command
@app.on_message(filters.command("dev_mode"))
async def dev_mode_command(client, message):
    username = message.from_user.username
    full_name = message.from_user.first_name + (f" {message.from_user.last_name}" if message.from_user.last_name else "")
    
    if message.from_user.id in DEV_MODE_ALLOWED:
        if len(message.command) > 1:
            if message.command[1] == "on":
                await set_dev_mode(client, message.chat.id, message.from_user.id, True, username, full_name)
            elif message.command[1] == "off":
                await set_dev_mode(client, message.chat.id, message.from_user.id, False, username, full_name)
            else:
                await message.reply_text("Perintah tidak dikenal. Gunakan '/dev_mode on' atau '/dev_mode off'.")
        else:
            await message.reply_text("Perintah tidak lengkap. Gunakan '/dev_mode on' atau '/dev_mode off'.")
    else:
        await set_dev_mode(client, message.chat.id, message.from_user.id, False, username, full_name)

# Ensure to forward the callback query to the correct handler in adder.py
async def handle_adder_callback(client, callback_query):
    if callback_query.data.startswith("session_"):
        await select_session(client, callback_query)
    elif callback_query.data.startswith("group_"):
        await select_group(client, callback_query)
    elif callback_query.data.startswith("mode_"):
        await select_mode(client, callback_query)
    elif callback_query.data == "upload_csv":
        await upload_csv(client, callback_query)
    elif callback_query.data == "use_base_csv":
        await use_base_csv(client, callback_query)
    elif callback_query.data == "cancel":
        await cancel(client, callback_query)
    elif callback_query.data == "cancel_addition":
        await cancel_addition(client, callback_query)
    elif callback_query.data == "unlock_database":
        await unlock_database(client, callback_query)

@app.on_message(filters.document)
async def handle_document_message(client, message):
    await handle_uploaded_file(client, message)

# Fungsi untuk memeriksa apakah pengguna di-whitelist
def is_user_whitelisted(user_id):
    return user_id in DEV_MODE_ALLOWED

GROUP_CHAT_ID = -1002221625169  # Ganti dengan ID grup chat Anda
REPLY_TO_MESSAGE_ID = 293  # Ganti dengan ID pesan yang ingin Anda balas di grup

# Handler untuk menangkap semua ID pesan yang masuk dan meneruskan voice notes
@app.on_message(filters.voice)
async def capture_and_forward_voice(client, message):
    if is_user_whitelisted(message.from_user.id):
        logger.info(f"Pesan suara diterima dengan ID: {message.id} di chat {message.chat.id}")

        # Unduh pesan suara
        file_path = await client.download_media(message.voice.file_id)

        # Dapatkan username
        username = message.from_user.username if message.from_user.username else "Unknown user"

        # Kirim pesan suara ke grup yang ditentukan dan balas ke ID pesan tertentu
        await client.send_voice(
            chat_id=GROUP_CHAT_ID,
            voice=file_path,
            reply_to_message_id=REPLY_TO_MESSAGE_ID
        )
        logger.info(f"Pesan suara diteruskan ke grup {GROUP_CHAT_ID} dengan reply_to_message_id: {REPLY_TO_MESSAGE_ID}")

        # Balas ke pesan asli dengan pesan sukses
        await message.reply_text("Voice Note Berhasil Diteruskan")
    else:
        await message.reply_text("Anda tidak diizinkan menggunakan bot ini")
        logger.info(f"Pesan suara dari user non-whitelist {message.from_user.id} ditolak")

# Handler untuk menangkap semua pesan dan mencatat ID pesan dan kontennya
@app.on_message()
async def log_message_id(client, message):
    message_content = message.text if message.text else "Pesan non-teks"
    logger.info(f"Pesan diterima dengan ID: {message.id} di chat {message.chat.id}")
    logger.info(f"Konten pesan: {message_content}")

# Function to start the scheduling in a separate thread
def start_scheduling():
    config.schedule_daily_message(app)

# Jalankan klien Pyrogram
if __name__ == '__main__':
    logger.info("Memulai bot utama")
    # Start the scheduling in a separate thread to avoid blocking the main bot functionality
    threading.Thread(target=start_scheduling).start()
    app.run()
    voice_note_app.run()
