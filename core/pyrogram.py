import os
from pyrogram import Client

session_name = 'Xylence'  # Ganti dengan cara Anda mengambil nama sesi

def create_pyrogram_client(SESSIONS_FOLDER, api_id, api_hash, bot_token):
    app = Client(
        os.path.join(SESSIONS_FOLDER, f'pyrogram_{session_name}'),  # Tentukan nama sesi dengan awalan "pyrogram_"
        api_id=api_id,
        api_hash=api_hash,
        bot_token=bot_token
    )
    return app
