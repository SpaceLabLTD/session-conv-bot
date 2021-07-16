import os
from pyrogram import Client
from dotenv import load_dotenv


load_dotenv()


if __name__ == "__main__":
    app = Client(
        ":memory:",
        api_id=os.environ.get("API_ID"),
        api_hash=os.environ.get("API_HASH"),
        bot_token=os.environ.get("BOT_TOKEN"),
        plugins=dict(root="modules"),
    )
    app.run()
