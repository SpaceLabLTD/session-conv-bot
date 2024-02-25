# MIT License

# Copyright (c) 2021 Md. Hasibul Kabir

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import logging
import sqlite3
from enum import Enum
from pathlib import Path
from uuid import uuid4

from aiogram import Bot, Router, html
from aiogram.filters import Command, CommandObject, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, Message
from fluxsession import SessionManager

event_router = Router()
logger = logging.getLogger(__name__)


@event_router.edited_message()
async def _skip_editing_messages(message: Message):
    await message.answer("Sorry, editing messages is not supported.")


class Session(StatesGroup):
    session_type = State()
    file_or_string = State()


class CommandsList(Enum):
    PYROGRAM_STRING_V3 = "pystring3"
    PYROGRAM_STRING_V2 = "pystring2"
    PYROGRAM_FILE_V3 = "pyfile3"
    TELETHON_STRING = "telestring"
    TELETHON_FILE = "telefile"

    @classmethod
    def list(cls):
        return [c.value for c in cls]


@event_router.message(Command(commands=CommandsList.list()))
async def request_handler(message: Message, state: FSMContext, command: CommandObject):
    await state.set_state(Session.file_or_string)
    await state.set_data({"session_type": command.command})
    await message.reply("Now send me session file or string.")


class SessionStringFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        return len(message.text) in [351, 353, 356, 362]


class SessionFileFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return (
            message.document
            and message.document.file_name
            and message.document.file_name.endswith(".session")
        )


async def guess_tdlib(session: str):
    conn, cursor = "", ""
    try:
        conn = sqlite3.connect(session, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = cursor.fetchall()
        for table in table_names:
            if table[0] in [
                "sessions",
                "entities",
                "sent_files",
                "update_state",
                "version",
            ]:
                continue
            else:
                break
        else:
            return "telethon"

        for table in table_names:
            if table[0] in ["sessions", "peers", "version"]:
                continue
            else:
                break
        else:
            return "pyrogram"

        return "unknown"  # noqa: TRY300

    except Exception:
        logger.exception("Error while guessing tdlib")
        return "unknown"

    finally:
        if conn and cursor:
            cursor.close()
            conn.close()


@event_router.message(Session.file_or_string, SessionStringFilter())
@event_router.message(Session.file_or_string, SessionFileFilter())
async def handle_file_or_string(message: Message, bot: Bot, state: FSMContext):  # noqa: C901, PLR0912
    file_path = f"{uuid4().hex}.session"
    try:
        session_type = (await state.get_data())["session_type"]
        if message.document and message.document.file_name.endswith(".session"):
            await bot.download(message.document.file_id, destination=file_path)

            tdlib = await guess_tdlib(file_path)
            if tdlib == "unknown":
                return await message.reply("Unknown session type.")

            elif tdlib == "telethon":
                manager = SessionManager.from_telethon_file(file_path)

            elif tdlib == "pyrogram":
                manager = SessionManager.from_pyrogram_session_file(file_path)

        elif message.text and len(message.text) in [351, 353, 356, 362]:
            if message.text.startswith("1"):
                manager = SessionManager.from_telethon_string_session(message.text)
            else:
                manager = SessionManager.from_pyrogram_string_session(message.text)

        else:
            return await message.reply("Unknown session type.")

        if session_type == CommandsList.PYROGRAM_STRING_V3.value:
            await message.reply(
                html.bold("Pyrogram string session:\n\n")
                + html.code(manager.pyrogram_string_session(version=3))
                + "\n"
                + html.bold("Version: 3"),
            )

        elif session_type == CommandsList.PYROGRAM_STRING_V2.value:
            await message.reply(
                html.bold("Pyrogram string session:\n\n")
                + html.code(manager.pyrogram_string_session(version=2))
                + "\n"
                + html.bold("Version: 2"),
            )

        elif session_type == CommandsList.PYROGRAM_FILE_V3.value:
            new_file_path = f"./{uuid4().hex[:8]}.session"
            try:
                manager.pyrogram_file(new_file_path, api_id=123456, user_id=123456)
                await message.reply_document(
                    FSInputFile(new_file_path),
                    caption=html.bold("Pyrogram v3"),
                )
            finally:
                Path(new_file_path).unlink()

        elif session_type == CommandsList.TELETHON_STRING.value:
            await message.reply(
                html.bold("Telethon string session:\n\n")
                + html.code(manager.telethon_string_session()),
            )

        elif session_type == CommandsList.TELETHON_FILE.value:
            new_file_path = f"./{uuid4().hex[:8]}.session"
            try:
                manager.telethon_file(new_file_path)
                await message.reply_document(
                    FSInputFile(new_file_path),
                    caption=html.bold("Telethon session file"),
                )
            finally:
                Path(new_file_path).unlink()

    except Exception as e:
        logging.exception("Error while handling file or string")
        await message.reply(f"Error: {e}")

    finally:
        await state.clear()
        file = Path(file_path)
        if file.exists():
            file.unlink()
