import os
from pyrogram import Client
from .pysession import Session
from pyrogram.types import CallbackQuery


@Client.on_callback_query()
async def process_callback_query(c: Client, cb: CallbackQuery):
    MAIN_SESSION = f"./downloads/{cb.from_user.id}.session"
    CONV_SESSION = f"./downloads/conv{cb.from_user.id}.session"
    session = Session()
    if os.path.isfile(MAIN_SESSION):
        name = await session.get_project_name(MAIN_SESSION)

        if name == "telethon":
            await session.load_telethon_session(MAIN_SESSION)

        if name == "pyrogram":
            await session.load_pyrogram_session(MAIN_SESSION)

    else:
        if cb.message.reply_to_message:
            SESSION_STRING = cb.message.reply_to_message.text
            if len(SESSION_STRING) >= 251 and SESSION_STRING[0] != "1":
                await session.load_pyrogram_session(SESSION_STRING)

            if len(SESSION_STRING) >= 251 and SESSION_STRING[0] == "1":
                await session.load_telethon_session(SESSION_STRING)

    if not session.loaded:
        await cb.edit_message_text("Failed to load session file.")

    else:
        if cb.data == "pyrogram_file":
            await session.generate_pyrogram_session_file(CONV_SESSION)

        elif cb.data == "telethon_file":
            await session.generate_telethon_session_file(CONV_SESSION)

        elif cb.data == "pyrogram_string":
            await cb.edit_message_text(
                "<b>Pyrogram Session:</b> <code>{}</code>".format(
                    await session.generate_string_pyrogram()
                )
            )

        elif cb.data == "telethon_string":
            await cb.edit_message_text(
                "<b>Telethon Session:</b> <code>{}</code>".format(
                    await session.generate_string_telethon()
                )
            )

    if os.path.isfile(CONV_SESSION):
        try:
            await c.send_document(
                chat_id=cb.from_user.id,
                document=CONV_SESSION,
                file_name="converted-session.session",
            )
            await cb.message.delete()
        except Exception:
            await cb.edit_message_text("Failed to send session file.")

    for i in [MAIN_SESSION, CONV_SESSION]:
        if os.path.isfile(i):
            os.remove(i)
