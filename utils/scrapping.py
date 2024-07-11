import os
import json
import csv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from telethon.sync import TelegramClient
from telethon.errors import ChatAdminRequiredError
from dotenv import load_dotenv

# Global variable to store selected session and groups
group_list_message = None
selected_session = None
group_data = []

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

# Function to fetch groups/channels from the selected session
async def get_groups_from_selected_session():
    global selected_session, group_data

    if not selected_session:
        return None, "No session selected."

    api_id = os.getenv('api_id')
    api_hash = os.getenv('api_hash')
    session_path = os.path.join('sessions', selected_session)
    client = TelegramClient(session_path, api_id, api_hash)

    try:
        await client.start()
        dialogs = await client.get_dialogs()
        group_list = []

        for dialog in dialogs:
            if dialog.is_group or dialog.is_channel:
                group_list.append({"name": dialog.name, "id": dialog.id})

        await client.disconnect()

        if group_list:
            group_data = group_list  # Set group_data with the found groups
            groups_text = "\n".join([f"{i + 1}. {group['name']} - {group['id']}" for i, group in enumerate(group_list)])
            return group_list, f"Group / Channel List from Session {selected_session}:\n{groups_text}"
        else:
            group_data = []  # Set group_data with empty list if no groups/channels found
            return [], f"No groups or channels found in Session {selected_session}."

    except Exception as e:
        return None, f"An error occurred: {str(e)}"

# Handler for /setgroup command
@Client.on_message(filters.command('setgroup'))
async def set_group_command(client, message):
    global selected_session, group_data
    sessions_folder = 'sessions'
    session_files = [fname for fname in os.listdir(sessions_folder) if fname.endswith('.session') and not fname.startswith('pyrogram_')]

    if not session_files:
        await message.reply_text("No sessions found.")
        return

    session_buttons = [
        [InlineKeyboardButton(text=session_file.replace('.session', ''), callback_data=f"select_session:{session_file.replace('.session', '')}")]
        for session_file in session_files
    ]
    reply_markup = InlineKeyboardMarkup(session_buttons)

    await message.reply_text("Select the session to use:", reply_markup=reply_markup)

# Handler for inline button of session selection
@Client.on_callback_query()
async def handle_callback_query(client, callback_query):
    global selected_session, group_data, group_list_message

    data = callback_query.data
    if data.startswith("select_session:"):
        selected_session = data.split("select_session:")[1] + '.session'
        sessions_folder = 'sessions'

        if selected_session not in os.listdir(sessions_folder):
            await callback_query.answer("Session not found.", show_alert=True)
            return

        await callback_query.answer(f"Session {selected_session} selected.")
        
        # Edit message to remove inline button
        await callback_query.message.edit_reply_markup(reply_markup=None)

        # After session is selected, call function to fetch groups/channels from Telethon
        group_data, result_text = await get_groups_from_selected_session()
        
        # Save reference to group list message
        group_list_message = await callback_query.message.reply_text(result_text)

        # Display question whether to perform scrapping
        await ask_for_scrapping(callback_query.message)

    elif data == "ya_scrapping" or data == "tidak_scrapping":
        session_name = selected_session.replace('.session', '')

        # Change the previous message to "Using session (Session Name)"
        if group_list_message:
            await group_list_message.edit_text(f"Using session: {session_name}")

        # After changing the message content, then remove the inline button
        await callback_query.message.edit_reply_markup(reply_markup=None)

        if data == "ya_scrapping":
            await handle_yes_scrapping(client, callback_query)
        else:
            await handle_no_scrapping(client, callback_query)

    elif data.startswith("group:"):
        group_id = int(data.split(":")[1])
        await handle_group_selection(client, callback_query, group_id)

    elif data.startswith("format:"):
        group_id = int(data.split(":")[1])
        file_format = data.split(":")[2]
        await handle_format_selection(client, callback_query, group_id, file_format)

    elif data == "continue_scrapping" or data == "stop_scrapping":
        await handle_continue_choice(client, callback_query)

# Function to ask whether the user wants to perform scrapping
async def ask_for_scrapping(message):
    await message.reply_text("Do you want to perform scrapping?",
                             reply_markup=InlineKeyboardMarkup([
                                 [InlineKeyboardButton("Yes", callback_data="ya_scrapping"),
                                  InlineKeyboardButton("No", callback_data="tidak_scrapping")]
                             ]))

# Function to create inline buttons from the group list
def create_group_buttons(group_list):
    group_buttons = [
        [InlineKeyboardButton(text=group['name'], callback_data=f"group:{group['id']}")]
        for group in group_list
    ]
    return InlineKeyboardMarkup(group_buttons)

# Function to handle 'yes' scrapping
async def handle_yes_scrapping(client, callback_query):
    global group_data
    if group_data:
        await callback_query.answer()
        await callback_query.message.reply_text("Select the group to scrap:",
                                                reply_markup=create_group_buttons(group_data))
    else:
        await callback_query.answer("No groups found for this session.", show_alert=True)

# Function to handle 'no' scrapping
async def handle_no_scrapping(client, callback_query):
    await callback_query.answer()
    await client.send_message(callback_query.message.chat.id, "Thank you. Scrapping process stopped.")

# Function to handle group selection
async def handle_group_selection(client, callback_query, group_id):
    global group_data

    # Find the selected group name
    selected_group = next((group for group in group_data if group['id'] == group_id), None)
    if selected_group:
        group_name = selected_group['name']
        group_id = selected_group['id']
    else:
        group_name = "Group not found"
        group_id = "ID not found"

    await callback_query.answer()
    
    # Remove the inline button for group
    await callback_query.message.edit_reply_markup(reply_markup=None)
    
    # Send message "Selecting (Group Name) - (Group ID)"
    await callback_query.message.reply_text(f"Selecting Group / Channel: {group_name}\nGroup ID: {group_id}")

    # Send message "Fetching group member data..."
    await callback_query.message.reply_text("Fetching group member data...")

    # Display file format selection
    await ask_for_file_format(callback_query.message, group_id)

# Function to ask the user to select the file format
async def ask_for_file_format(message, group_id):
    await message.reply_text("Select the file format to save member data:",
                             reply_markup=InlineKeyboardMarkup([
                                 [InlineKeyboardButton("TXT", callback_data=f"format:{group_id}:txt"),
                                  InlineKeyboardButton("CSV", callback_data=f"format:{group_id}:csv")]
                             ]))

# Function to handle file format selection and send the document
async def handle_format_selection(client, callback_query, group_id, file_format):
    await callback_query.answer()
    
    # Remove the inline button for file format
    await callback_query.message.edit_reply_markup(reply_markup=None)

    # Send a message "Fetching group member data..."
    await callback_query.message.reply_text("Fetching group member data...")

    # Call the function to fetch group member data
    member_data = await get_group_members(group_id, callback_query.message)

    if file_format == "txt":
        # Save group member data to .txt file
        file_path = save_members_to_file(member_data)
    elif file_format == "csv":
        # Save group member data to .csv file
        file_path = save_members_to_csv(member_data)
    
    # Check if the file size is greater than 0 bytes before sending it
    if os.path.getsize(file_path) > 0:
        # Send the file to the user
        await client.send_document(callback_query.message.chat.id, file_path)
    else:
        await callback_query.message.reply_text("Failed to fetch group member data or no data available.")

    # Ask if the user wants to continue scrapping
    await ask_continue_scrapping(callback_query.message)

# Function to ask the user if they want to continue scrapping
async def ask_continue_scrapping(message):
    await message.reply_text(
        "Do you want to continue scrapping?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Yes", callback_data="continue_scrapping"),
             InlineKeyboardButton("No", callback_data="stop_scrapping")]
        ])
    )

# Function to handle the user's choice to continue or stop scrapping
async def handle_continue_choice(client, callback_query):
    await callback_query.answer()
    
    # Remove the inline button after user choice
    await callback_query.message.edit_reply_markup(reply_markup=None)

    if callback_query.data == "continue_scrapping":
        await handle_yes_scrapping(client, callback_query)
    else:
        await callback_query.message.reply_text("Thank you. Scrapping process stopped.")

# Function to fetch group member data
async def get_group_members(group_id, message):
    global selected_session

    if not selected_session:
        return []

    api_id = os.getenv('api_id')
    api_hash = os.getenv('api_hash')
    session_path = os.path.join('sessions', selected_session)
    client = TelegramClient(session_path, api_id, api_hash)

    members = []
    try:
        await client.start()
        async for member in client.iter_participants(group_id):
            if member.access_hash:
                members.append({
                    'id': member.id,
                    'username': member.username or 'N/A',
                    'access_hash': member.access_hash,
                    'first_name': member.first_name or 'N/A',
                    'last_name': member.last_name or 'N/A',
                    'phone': member.phone or 'N/A'
                })
        await client.disconnect()
    except ChatAdminRequiredError:
        await message.reply_text("Chat admin privileges are required.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")

    return members

# Function to save members to a .txt file
def save_members_to_file(members):
    file_path = "group_members.txt"
    with open(file_path, "w", encoding="utf-8") as file:
        for member in members:
            username = member['username']
            user_id = member['id']
            access_hash = member['access_hash']
            first_name = member['first_name']
            last_name = member['last_name']
            phone = member['phone']
            
            file.write(f"Username: {username}, ID: {user_id}, Access Hash: {access_hash}, First Name: {first_name}, Last Name: {last_name}, Phone: {phone}\n")
    return file_path

# Function to save members to a .csv file
def save_members_to_csv(members):
    file_path = "group_members.csv"
    with open(file_path, "w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Username", "ID", "Access Hash", "First Name", "Last Name", "Phone"])
        for member in members:
            writer.writerow([
                member['username'] if member['username'] != 'N/A' else '',
                member['id'],
                member['access_hash'],
                member['first_name'] if member['first_name'] != 'N/A' else '',
                member['last_name'] if member['last_name'] != 'N/A' else '',
                member['phone'] if member['phone'] != 'N/A' else ''
            ])
    return file_path
