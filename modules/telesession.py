from .pysession import Session

from pyrogram import (
    Client,
    filters,
)

from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


@Client.on_message(
    filters.text
    & filters.private
    & filters.create(
        lambda _, __, m: m.text and len(m.text) == 353 and m.text[0] == "1"
    )
)
async def telethon_to_python(_: Client, m: Message):
    session = Session()
    await session.load_telethon_session(m.text)
    if not session.loaded:
        await m.reply_text(
            "Sorry, Something went wrong. Can not convert string session."
        )

    else:
        await m.reply_text(
            "<b>Pyrogram Session:</b> <code>{}</code>".format(
                await session.generate_string_pyrogram()
            ),
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
                            "Telethon Session", callback_data="telethon_file"
                        )
                    ],
                ]
            ),
        )
