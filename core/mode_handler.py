import logging
import os
from pyrogram import Client

logger = logging.getLogger(__name__)

# Define commands for each mode
NORMAL_COMMANDS = ["/start", "/get_id", "/getgroupid"]
DEV_COMMANDS = ["/start", "/get_id", "/getgroupid", "/forward", "/forward_all", "/createsession", "/scr_group", "/adder_group"]

# Variable to track the current mode
dev_mode = False

# Daftar user ID yang di-whitelist
DEV_MODE_ALLOWED = [
    6320998144,  # ID user monarchiv
    1238655724,  # ID user XylenceOMX
    7180227348,  # ID User XylenceXY
    0,  # 
    # Tambahkan user ID lainnya di bawah ini
]


# Load the USER_ID for warnings from environment variable
WARNING_USER_ID = int(os.getenv('USER_ID', '0'))

async def set_dev_mode(client: Client, chat_id: int, user_id: int, value: bool, username: str, full_name: str):
    global dev_mode

    if user_id not in DEV_MODE_ALLOWED:
        warning_message = f"Pengguna tidak terdaftar mencoba mengaktifkan dev mode:\nUsername: {username}\nUser ID: {user_id}\nNama: {full_name}"
        await client.send_message(WARNING_USER_ID, warning_message)
        return

    dev_mode = value
    mode_status = 'ON' if dev_mode else 'OFF'
    logger.info(f"Dev mode set to {mode_status}")

    # Prepare the message
    if dev_mode:
        commands_list = "\n".join(DEV_COMMANDS)
        message = f"Dev mode diaktifkan. Perintah yang tersedia:\n{commands_list}"
    else:
        commands_list = "\n".join(NORMAL_COMMANDS)
        message = f"Dev mode dinonaktifkan. Perintah yang tersedia:\n{commands_list}"

    # Send the message to the user
    await client.send_message(chat_id, message)

def is_command_allowed(command: str) -> bool:
    if dev_mode:
        return command in DEV_COMMANDS or command in NORMAL_COMMANDS
    else:
        return command in NORMAL_COMMANDS
