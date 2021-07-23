from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


@Client.on_message(filters.command(["start"]))
async def start_command(_: Client, m: Message):
    await m.reply_text(
        "Welcome. This is session converter bot."
        "I can convert telethon session to pyrogram session and pyrogram session to telethon session. "
        "Just send me a string session. I will Try to convert it.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Source Code 😍",
                        url="https://github.com/HKPROJECTS/session-conv-bot",
                    ),
                ]
            ]
        ),
    )
