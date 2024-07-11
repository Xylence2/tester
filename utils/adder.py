import json
import os
import sys
import csv
import traceback
import time
import random
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import sqlite3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use the same variable names as in your JSON file
TOKEN_BOT_UTAMA = os.getenv('TOKEN_BOT_UTAMA')
ID_AKUN_UTAMA = os.getenv('USERNAME_MAIN_ACCOUNT')
GROUP_ID = int(os.getenv('GROUP_ID'))
api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')
phone = os.getenv('phone')

# RetryMessageManager to manage retry messages
class RetryMessageManager:
    def __init__(self, bot, chat_id):
        self.bot = bot
        self.chat_id = chat_id
        self.current_message_id = None

    async def send_retry_message(self, text):
        # Edit the existing message if it exists
        if self.current_message_id:
            await self.bot.edit_message_text(self.chat_id, self.current_message_id, text)
        else:
            # Send a new message if none exists
            new_message = await self.bot.send_message(self.chat_id, text)
            self.current_message_id = new_message.id

# Function to fetch groups/channels from the selected session
async def get_groups_from_selected_session(selected_session, message):
    session_path = os.path.join(sessions_folder, selected_session)
    client = TelegramClient(session_path, api_id, api_hash)

    retry_manager = RetryMessageManager(bot, message.chat.id)
    retries = 5
    delay = 10

    for attempt in range(retries):
        try:
            await client.start()

            # Fetch group chats
            chats = []
            last_date = None
            chunk_size = 200
            groups = []

            result = await client(GetDialogsRequest(
                offset_date=last_date,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=chunk_size,
                hash=0
            ))
            chats.extend(result.chats)

            for chat in chats:
                try:
                    if chat.megagroup:
                        groups.append(chat)
                except:
                    continue

            return client, groups
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                await retry_manager.send_retry_message(f"Database is locked, retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
                await asyncio.sleep(delay)
            else:
                raise
    raise Exception("Failed to start client after several retries due to locked database")

# Function to add users to the selected group
cancel_addition = False

async def add_users_to_group(client, target_group_entity, users, mode, message):
    global cancel_addition
    cancel_addition = False  # Reset the cancellation flag

    n = 0
    SLEEP_TIME_2 = 60 * 60  # Define SLEEP_TIME_2 (e.g., 1 hour)

    # Create cancel button
    buttons = [[InlineKeyboardButton("Batal", callback_data="cancel_addition")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply("Menambahkan anggota... Klik tombol di bawah untuk membatalkan:", reply_markup=reply_markup)

    retry_manager = RetryMessageManager(message._client, message.chat.id)

    for user in users:
        if cancel_addition:
            await message.reply("Proses penambahan anggota dibatalkan.")
            break

        n += 1
        if n % 80 == 0:
            await asyncio.sleep(60)  # Use asyncio.sleep instead of sleep

        try:
            print(f"Adding {user['id']}")
            if mode == 1:
                if user['username'] == "":
                    continue
                user_to_add = await client.get_input_entity(user['username'])
            elif mode == 2:
                user_to_add = InputPeerUser(user['id'], user['access_hash'])
            else:
                sys.exit("Invalid Mode Selected. Please Try Again.")
            await client(InviteToChannelRequest(target_group_entity, [user_to_add]))
            print("Waiting for 60-180 Seconds...")
            await asyncio.sleep(random.randrange(60, 180))  # Adjusted range to 60-180 seconds
        except PeerFloodError:
            print("Getting Flood Error from telegram. Script is stopping now. Please try again after some time.")
            print(f"Waiting {SLEEP_TIME_2} seconds")
            await asyncio.sleep(SLEEP_TIME_2)  # Use asyncio.sleep instead of sleep
        except UserPrivacyRestrictedError:
            print("The user's privacy settings do not allow you to do this. Skipping.")
            print("Waiting for 5 Seconds...")
            await asyncio.sleep(random.randrange(5, 10))  # Adjusted range to 5-10 seconds
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                await retry_manager.send_retry_message("Database is locked, retrying in 10 seconds...")
                await asyncio.sleep(10)
                continue
            else:
                raise
        except:
            traceback.print_exc()
            print("Unexpected Error")
            continue

    if not cancel_addition:
        await message.reply("Semua Anggota Telah Ditambahkan.")
    print("Finished adding all users.")

# Ensure the sessions folder exists
sessions_folder = os.path.abspath('sessions')
os.makedirs(sessions_folder, exist_ok=True)

# Check for an existing session file that contains "pyrogram_" in its name
session_files = [fname for fname in os.listdir(sessions_folder) if 'pyrogram_' in fname and fname.endswith('.session')]

# Determine the session name
if session_files:
    # Use the first found session file containing "pyrogram_"
    session_name = os.path.splitext(session_files[0])[0]
else:
    # Create a new session name if no existing session is found
    session_name = 'pyrogram_new_session'

# Construct the full path for the session file
session_path = os.path.join(sessions_folder, session_name + '.session')

# Initialize the Pyrogram Client
bot = Client(session_path, api_id=api_id, api_hash=api_hash, bot_token=TOKEN_BOT_UTAMA)

sessions_folder = 'sessions'
os.makedirs(sessions_folder, exist_ok=True)
session_files = [fname for fname in os.listdir(sessions_folder) if fname.endswith('.session')]

selected_session = None
target_group = None
mode = None
groups = []

@bot.on_message(filters.command("adder_group"))
async def adder_group(client, message):
    buttons = [
        [InlineKeyboardButton(session.replace('.session', ''), callback_data=f"session_{i}")]
        for i, session in enumerate(session_files) if 'pyrogram' not in session
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply("Welcome! Please select a session by clicking a button below:", reply_markup=reply_markup)

@bot.on_callback_query(filters.regex(r"^session_(\d+)$"))
async def select_session(client, callback_query):
    global selected_session
    index = int(callback_query.data.split("_")[1])
    selected_session = session_files[index]
    await callback_query.message.edit_text(f'Selected session: {selected_session}')
    await fetch_groups(callback_query.message)

async def fetch_groups(message):
    global groups
    _, groups = await get_groups_from_selected_session(selected_session, message)
    if not groups:
        await message.reply('No groups found.')
        return
    buttons = [
        [InlineKeyboardButton(f"{i}: {group.title}", callback_data=f"group_{i}")]
        for i, group in enumerate(groups)
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply("Choose a group by clicking a button below:", reply_markup=reply_markup)

@bot.on_callback_query(filters.regex(r"^group_(\d+)$"))
async def select_group(client, callback_query):
    global target_group
    index = int(callback_query.data.split("_")[1])
    target_group = groups[index]
    await callback_query.message.edit_text(f'Selected group: {target_group.title}')
    buttons = [
        [InlineKeyboardButton("Username", callback_data="mode_1")],
        [InlineKeyboardButton("ID", callback_data="mode_2")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await callback_query.message.reply("Enter 1 to add by username or 2 to add by ID:", reply_markup=reply_markup)

@bot.on_callback_query(filters.regex(r"^mode_(\d+)$"))
async def select_mode(client, callback_query):
    global mode
    mode = int(callback_query.data.split("_")[1])
    await callback_query.message.edit_text(f'Selected mode: {mode}')
    buttons = [
        [InlineKeyboardButton("Upload CSV", callback_data="upload_csv")],
        [InlineKeyboardButton("Use Base CSV", callback_data="use_base_csv")],
        [InlineKeyboardButton("Batal", callback_data="cancel")],
        [InlineKeyboardButton("Unlock Database", callback_data="unlock_database")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await callback_query.message.reply("Choose how to provide the members list:", reply_markup=reply_markup)

@bot.on_callback_query(filters.regex(r"^upload_csv$"))
async def upload_csv(client, callback_query):
    await callback_query.message.edit_text("Please upload the CSV file with members.")

@bot.on_callback_query(filters.regex(r"^use_base_csv$"))
async def use_base_csv(client, callback_query):
    await callback_query.message.edit_text("Memulai proses...")
    await handle_csv_file(callback_query.message, "group_members.csv")

@bot.on_callback_query(filters.regex(r"^cancel$"))
async def cancel(client, callback_query):
    await callback_query.message.edit_text("Perintah /adder_group dibatalkan.")

@bot.on_callback_query(filters.regex(r"^cancel_addition$"))
async def cancel_addition(client, callback_query):
    global cancel_addition
    cancel_addition = True
    await callback_query.message.edit_text("Proses penambahan anggota dibatalkan.")

@bot.on_callback_query(filters.regex(r"^unlock_database$"))
async def unlock_database(client, callback_query):
    await callback_query.message.edit_text("Mengecek status database...")
    if await is_database_locked():
        await perform_unlock_database(callback_query.message)
    else:
        await callback_query.message.edit_text("Database tidak terkunci.")

async def is_database_locked():
    # Function to check if the database is locked
    try:
        # Attempt to connect to the database
        conn = sqlite3.connect('sessions/your_database.db')  # Replace with your database path
        conn.execute('SELECT 1')
        conn.close()
        return False
    except sqlite3.OperationalError as e:
        if 'database is locked' in str(e):
            return True
        else:
            raise e

async def perform_unlock_database(message):
    retries = 5
    delay = 10
    retry_manager = RetryMessageManager(message._client, message.chat.id)

    for attempt in range(retries):
        try:
            # Attempt to unlock the database by connecting and performing a dummy operation
            conn = sqlite3.connect('sessions/your_database.db')  # Replace with your database path
            conn.execute('SELECT 1')
            conn.close()
            await message.reply("Database berhasil dibuka.")
            return
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                await retry_manager.send_retry_message(f"Database is locked, retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
                await asyncio.sleep(delay)
            else:
                raise
    await message.reply("Failed to unlock database after several retries.")

@bot.on_message(filters.document)
async def handle_uploaded_file(client, message):
    if not selected_session or not target_group or not mode:
        await message.reply("Please complete the previous steps before uploading the CSV file.")
        return
    if not message.document.file_name.endswith('.csv'):
        await message.reply("Please upload a CSV file.")
        return
    file_path = await message.download()
    await message.reply("Terima kasih. Memulai perintah...")
    await handle_csv_file(message, file_path)

async def handle_csv_file(message, file_path):
    users = []
    with open(file_path, encoding='UTF-8') as f:
        rows = csv.reader(f, delimiter=",", lineterminator="\n")
        next(rows, None)
        for row in rows:
            user = {'username': row[0], 'id': int(row[1]), 'access_hash': int(row[2]), 'name': row[3]}
            users.append(user)

    session_path = os.path.join(sessions_folder, selected_session)
    client = TelegramClient(session_path, api_id, api_hash)

    retries = 5
    delay = 10
    retry_manager = RetryMessageManager(message._client, message.chat.id)

    for attempt in range(retries):
        try:
            await client.start()
            break
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                await retry_manager.send_retry_message(f"Database is locked, retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
                await asyncio.sleep(delay)
            else:
                raise
    else:
        await message.reply("Failed to start client after several retries due to locked database")
        raise Exception("Failed to start client after several retries due to locked database")

    try:
        target_group_entity = InputPeerChannel(target_group.id, target_group.access_hash)
        await add_users_to_group(client, target_group_entity, users, mode, message)
    finally:
        await client.disconnect()
    print("Completed the addition process for all users.")

if __name__ == "__main__":
    bot.run()