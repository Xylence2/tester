import logging
import datetime
import pytz
import asyncio
import schedule
import time
import re
import threading
from pyrogram import Client

# Variabel global
LAST_MESSAGE_ID_WITH_DATE = None
LAST_MESSAGE_ID_WITH_GET_ID_DATE = None
CHANNEL_ID = -1002169168287
DISCUSS_GROUP = -1002201121650
AVAILABLE_COMMANDS = ["/start", "/get_id"]

# Variabel untuk mengontrol pemantauan pesan
monitoring_messages = False

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Fungsi untuk mengirim pesan otomatis
def send_daily_message(app: Client):
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    current_date = datetime.datetime.now(jakarta_tz).strftime('%Y-%m-%d')
    message_text_start = f"Data pengguna (start) pada tanggal {current_date}"
    message_text_get_id = f"Data pengguna (Get_ID) pada tanggal {current_date}"
    
    async def send_messages():
        await app.send_message(CHANNEL_ID, message_text_start)
        await app.send_message(CHANNEL_ID, message_text_get_id)
    
    asyncio.run(send_messages())

# Fungsi untuk memulai pemantauan pesan
def start_monitoring_messages():
    global monitoring_messages
    monitoring_messages = True
    logger.info("Mulai memantau pesan selama 5 menit sebelum pengiriman pesan otomatis.")

# Jadwalkan pesan harian pada waktu tertentu (misalnya, jam 9:09 dan 9:10 pagi waktu Jakarta)
def schedule_daily_message(app: Client):
    schedule.every().day.at("10:05").do(start_monitoring_messages)  # Mulai memantau pesan 5 menit sebelum pengiriman
    schedule.every().day.at("10:06").do(lambda: send_daily_message(app))  # Kirim pesan otomatis setiap hari

    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    # Jalankan penjadwalan di thread terpisah
    threading.Thread(target=run_schedule).start()

# Fungsi untuk menangani pesan di DISCUSS_GROUP
async def handle_message(client, message):
    global LAST_MESSAGE_ID_WITH_DATE, LAST_MESSAGE_ID_WITH_GET_ID_DATE

    date_pattern = r'\b(?:\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{4})\b'
    
    if re.search(date_pattern, message.text):
        if "start" in message.text.lower():
            LAST_MESSAGE_ID_WITH_DATE = message.id
            logger.info(f"Message with 'start' and date detected. Message ID: {message.id}")
            logger.info(f"Text: {message.text}")
        
        elif "GET_ID" in message.text.upper():
            LAST_MESSAGE_ID_WITH_GET_ID_DATE = message.id
            logger.info(f"Message with 'GET_ID' and date detected. Message ID: {message.id}")
            logger.info(f"Text: {message.text}")
