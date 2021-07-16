import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from .converter import telethon_to_pyrogram

from pyrogram import (
    Client,
    filters,
)

from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


user_response = {}


@Client.on_message(
    filters.text
    & filters.private
    & filters.create(
        lambda _, __, m: m.text and len(m.text) == 353 and m.text[0] == "1"
    )
)
async def ___(_, m):
    await m.reply_text(
        "KO. Now you have to provide two answer.",
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Use Automatic Change", callback_data="automatic"
                    )
                ],
                [InlineKeyboardButton("Provide User ID", callback_data="manual")],
            ]
        ),
    )


@Client.on_message(filters.command("cancel"))
async def ____(_, m):
    if m.from_user.id in user_response:
        del user_response[m.from_user.id]
        await m.reply_text("Process cancelled.")
    else:
        await m.reply_text("No context found for you.")


async def __user_id_filter(_, __, m):
    if m.from_user and m.from_user.id in user_response:
        if m.text and len(m.text) >= 5 and len(m.text) < 15:
            return m.text.isdigit()
    return False


@Client.on_message(filters.create(__user_id_filter) & filters.private)
async def _____(_, m):
    cb = user_response[m.from_user.id]["resp"]
    await m.delete()
    user_response[m.from_user.id]["userid"] = m.text
    await cb.edit_message_text(
        "Is this session belong to a bot?",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Yes", callback_data="bot")],
                [InlineKeyboardButton("No", callback_data="user")],
            ]
        ),
    )


@Client.on_callback_query()
async def ______(_, cb):
    if cb.data == "automatic":
        async with TelegramClient(
            StringSession(cb.message.reply_to_message.text),
            api_id=os.environ.get("TELETHON_APP_ID"),
            api_hash=os.environ.get("TELETHON_API_HASH"),
        ) as client:
            user = await client.get_me()
            await cb.edit_message_text(
                "<b>Pyrogram Session:</b> <code>{}</code>".format(
                    await telethon_to_pyrogram(
                        cb.message.reply_to_message.text,
                        int(user.id),
                        int(user.bot),
                    )
                )
            )

    elif cb.data == "manual":
        user_response[cb.from_user.id] = {
            "session": cb.message.reply_to_message.text,
            "resp": cb,
        }
        await cb.edit_message_text(
            "Now send me userid of this session string.\n"
            "You can't go back you have to start from sending session if you mistake. "
            "You can use /cancel at any time."
        )

    elif cb.data == "bot":
        try:
            await cb.edit_message_text(
                "<b>Pyrogram Session:</b> <code>{}</code>".format(
                    await telethon_to_pyrogram(
                        user_response[cb.from_user.id]["session"],
                        user_response[cb.from_user.id]["userid"],
                        True,
                    )
                )
            )
        except KeyError:
            await cb.edit_message_text(
                "Session expied. Please try from sending session again."
            )

    elif cb.data == "user":
        try:
            await cb.edit_message_text(
                "<b>Pyrogram Session:</b> <code>{}</code>".format(
                    await telethon_to_pyrogram(
                        user_response[cb.from_user.id]["session"],
                        user_response[cb.from_user.id]["userid"],
                        False,
                    )
                )
            )
        except KeyError:
            await cb.edit_message_text(
                "Session expied. Please try from sending session again."
            )
