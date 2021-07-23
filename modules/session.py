import os

from pyrogram import (
    Client,
    filters,
)
from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from .pysession import Session


@Client.on_message(
    filters.document
    & filters.private
    & filters.create(
        lambda _, __, m: m.document
        and m.document.file_name
        and m.document.file_name.endswith(".session")
    )
)
async def process_document_session(_: Client, m: Message):
    user_session_name = await m.download(f"{m.from_user.id}.session")
    session = Session()
    name = await session.get_project_name(user_session_name)
    if name == "telethon":
        await m.reply_text(
            "Your current session created from Telethon.",
            quote=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Pyrogram Session", callback_data="pyrogram_file"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "Pyrogram String", callback_data="pyrogram_string"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "Telethon String", callback_data="telethon_string"
                        )
                    ],
                ]
            ),
        )

    elif name == "pyrogram":
        await m.reply_text(
            "Your current session created from Pyrogram.",
            quote=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Telethon Session", callback_data="telethon_file"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "Telethon String", callback_data="telethon_string"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "Pyrogram String", callback_data="pyrogram_string"
                        )
                    ],
                ]
            ),
        )

    else:
        await m.reply_text("Sorry, I don't think it's a valid session.")
        os.remove(user_session_name)
