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


import os
import struct
import base64
import sqlite3
import ipaddress

from pyrogram import Client


class Session:
    def __init__(
        self,
        auth_key: bytes = None,
        server_address: str = None,
        port: int = None,
        user_id: int = None,
        is_bot: int = None,
        dc_id: int = None,
        test_mode: int = None,
    ):
        self._auth_key = auth_key
        self._server_adderss = server_address
        self._port = port
        self._user_id = user_id
        self._is_bot = is_bot
        self._dc_id = dc_id
        self._test_mode = test_mode
        self._takeout_id = None  # Not required for pyrogram or telethon
        self._loaded = False

    @property
    def loaded(self):
        return self._loaded

    @property
    def test_mode(self):
        if self._port is not None:
            return self._port == 80
        return self._test_mode

    @property
    def dc_id(self):
        return self._dc_id

    @property
    def user_id(self):
        return self._user_id

    @property
    def is_bot(self):
        return self._is_bot

    @property
    def auth_key(self):
        return self._auth_key

    @property
    def takeout_id(self):
        return self._takeout_id

    @property
    def port(self):
        if self._port is None and self.test_mode is not None:
            return 80 if self.test_mode else 443
        return self._port

    @property
    def server_address(self):
        if self._server_adderss is None and self.dc_id is not None:
            TEST = {
                1: "149.154.175.10",
                2: "149.154.167.40",
                3: "149.154.175.117",
                121: "95.213.217.195",
            }
            PROD = {
                1: "149.154.175.53",
                2: "149.154.167.51",
                3: "149.154.175.100",
                4: "149.154.167.91",
                5: "91.108.56.130",
                121: "95.213.217.195",
            }
            self._server_adderss = (
                TEST[self.dc_id] if self.test_mode else PROD[self.dc_id]
            )
        return self._server_adderss

    async def load_user(self):
        async with Client(
            await self.generate_string_pyrogram(True),
            api_id=os.environ.get("MULTI_APP_ID"),
            api_hash=os.environ.get("MULTI_API_HASH"),
        ) as client:
            user = await client.get_me()
            self._user_id = user.id
            self._is_bot = user.is_bot

    async def load_telethon_session(self, session: str):
        try:
            if len(session) < 251 and os.path.exists(session):
                conn = sqlite3.connect(session, check_same_thread=False)
                (
                    self._dc_id,
                    ip,
                    self._port,
                    self._auth_key,
                    self._takeout_id,
                ) = conn.execute("select * from sessions").fetchone()
                self._server_adderss = ipaddress.ip_address(ip).compressed
                self._loaded = True
                conn.close()

            elif not os.path.exists(session):
                if session[0] == "1":
                    session = session[1:]

                self._dc_id, ip, self._port, self._auth_key = struct.unpack(
                    ">B4sH256s",
                    base64.urlsafe_b64decode(session + "=" * (-len(session) % 4)),
                )
                self._server_adderss = ipaddress.ip_address(ip).compressed
                self._loaded = True

        finally:
            return self._loaded

    async def load_pyrogram_session(self, session: str):
        try:
            if len(session) < 251 and os.path.exists(session):
                conn = sqlite3.connect(session, check_same_thread=False)
                (
                    self._dc_id,
                    self._test_mode,
                    self._auth_key,
                    self._date,
                    self._user_id,
                    self._is_bot,
                ) = conn.execute("select * from sessions").fetchone()
                self._loaded = True
                conn.close()

            elif not os.path.exists(session):
                (
                    self._dc_id,
                    self._test_mode,
                    self._auth_key,
                    self._user_id,
                    self._is_bot,
                ) = struct.unpack(
                    ">B?256sI?",
                    base64.urlsafe_b64decode(session + "=" * (-len(session) % 4)),
                )
                self._loaded = True

        finally:
            return self._loaded

    async def generate_string_pyrogram(self, noload_user: bool = False):
        if not self.loaded:
            raise ValueError("Session not loaded")

        if not self.user_id and not noload_user:
            await self.load_user()

        return (
            base64.urlsafe_b64encode(
                struct.pack(
                    ">B?256sI?",
                    self.dc_id,
                    self.test_mode,
                    self.auth_key,
                    int(self.user_id or 999999999),
                    int(self.is_bot or 0),
                )
            )
            .decode()
            .rstrip("=")
        )

    async def generate_string_telethon(self):
        if not self.loaded:
            raise ValueError("Session not loaded")

        ip_address = ipaddress.ip_address(self.server_address).packed
        return (
            "1"
            + base64.urlsafe_b64encode(
                struct.pack(
                    ">B{}sH256s".format(len(ip_address)),
                    self.dc_id,
                    ip_address,
                    self.port,
                    self.auth_key,
                )
            ).decode("ascii")
        )

    async def generate_string_gramjs(self):
        # Reason: It's core based on Telethon. So It should be same as it.
        return await self.generate_string_telethon()

    async def get_project_name(self, session: str):
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

            return "unknown"

        except Exception:
            return "unknown"

        finally:
            if conn and cursor:
                cursor.close()
                conn.close()

    async def generate_pyrogram_session_file(self, session_path: str):
        if not self.loaded:
            raise ValueError("Session not loaded")

        if os.path.exists(session_path):
            os.remove(session_path)

        conn = sqlite3.connect(session_path, check_same_thread=False)
        conn.executescript(SCHEMA)
        conn.execute("INSERT INTO version VALUES (?)", (2,))
        conn.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?)",
            (2, None, None, 0, None, None),
        )
        if self.user_id is None:
            await self.load_user()

        items = {
            "dc_id": self.dc_id,
            "test_mode": self.test_mode,
            "auth_key": self.auth_key,
            "user_id": self.user_id,
            "date": 0,
            "is_bot": self.is_bot,
        }
        for k, v in items.items():
            conn.execute(f"UPDATE sessions SET {k} = ?", (v,))
        conn.commit()
        conn.close()
        return True

    async def generate_telethon_session_file(self, session_path: str):
        if not self.loaded:
            raise ValueError("Session not loaded")

        if os.path.exists(session_path):
            os.remove(session_path)

        conn = sqlite3.connect(session_path, check_same_thread=False)
        for table in TELETHON_TABLES:
            conn.execute("create table if not exists {}".format(table))

        conn.execute("insert into version values (?)", (7,))
        conn.execute(
            "insert or replace into sessions values (?,?,?,?,?)",
            (
                self.dc_id,
                self.server_address,
                self.port,
                self.auth_key,
                self.takeout_id,
            ),
        )
        conn.commit()
        conn.close()
        return True


SCHEMA = """
CREATE TABLE sessions
(
    dc_id     INTEGER PRIMARY KEY,
    test_mode INTEGER,
    auth_key  BLOB,
    date      INTEGER NOT NULL,
    user_id   INTEGER,
    is_bot    INTEGER
);

CREATE TABLE peers
(
    id             INTEGER PRIMARY KEY,
    access_hash    INTEGER,
    type           INTEGER NOT NULL,
    username       TEXT,
    phone_number   TEXT,
    last_update_on INTEGER NOT NULL DEFAULT (CAST(STRFTIME('%s', 'now') AS INTEGER))
);

CREATE TABLE version
(
    number INTEGER PRIMARY KEY
);

CREATE INDEX idx_peers_id ON peers (id);
CREATE INDEX idx_peers_username ON peers (username);
CREATE INDEX idx_peers_phone_number ON peers (phone_number);

CREATE TRIGGER trg_peers_last_update_on
    AFTER UPDATE
    ON peers
BEGIN
    UPDATE peers
    SET last_update_on = CAST(STRFTIME('%s', 'now') AS INTEGER)
    WHERE id = NEW.id;
END;
"""


TELETHON_TABLES = [
    "version (version integer primary key)",
    """sessions (
                dc_id integer primary key,
                server_address text,
                port integer,
                auth_key blob,
                takeout_id integer
            )""",
    """entities (
                id integer primary key,
                hash integer not null,
                username text,
                phone integer,
                name text,
                date integer
            )""",
    """sent_files (
                md5_digest blob,
                file_size integer,
                type integer,
                id integer,
                hash integer,
                primary key(md5_digest, file_size, type)
            )""",
    """update_state (
                id integer primary key,
                pts integer,
                qts integer,
                date integer,
                seq integer
            )""",
]
