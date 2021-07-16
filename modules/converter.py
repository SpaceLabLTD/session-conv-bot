import base64
import struct
import ipaddress


async def telethon_to_pyrogram(session: str, user_id: int = None, is_bot: str = False):
    session = session[1:] if session[0] == "1" else session
    dc_id, _, port, auth_key = struct.unpack(
        ">B4sH256s",
        base64.urlsafe_b64decode(session + "=" * (-len(session) % 4)),
    )
    return (
        base64.urlsafe_b64encode(
            struct.pack(
                ">B?256sI?",
                dc_id,
                port == 80,
                auth_key,
                int(user_id),
                int(is_bot),
            )
        )
        .decode()
        .rstrip("=")
    )


async def pyrogram_to_telethon(session: str):
    dc_id, test_mode, auth_key, _, _ = struct.unpack(
        ">B?256sI?", base64.urlsafe_b64decode(session + "=" * (-len(session) % 4))
    )
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
    server_address, port = (TEST[dc_id], 80) if test_mode else (PROD[dc_id], 443)
    ip_address = ipaddress.ip_address(server_address).packed
    return (
        "1"
        + base64.urlsafe_b64encode(
            struct.pack(
                ">B{}sH256s".format(len(ip_address)),
                dc_id,
                ip_address,
                port,
                auth_key,
            )
        ).decode("ascii")
    )
