from pyrogram import (
    Client,
    filters,
)
from .converter import pyrogram_to_telethon


@Client.on_message(
    filters.text
    & filters.private
    & filters.create(
        lambda f, c, m: m.text and len(m.text) >= 248 and len(m.text) < 353
    )
)
async def ___(_, m):
    try:
        await m.reply_text(
            "<b>Telethon Session:</b> <code>{}</code>".format(
                await pyrogram_to_telethon(m.text)
            )
        )

    except Exception:
        await m.reply_text(
            "Sorry, Something went wrong. Can not convert string session."
        )
