import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from modules.setup import setup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
load_dotenv()


async def main():
    app = Bot(getenv("TELEGRAM_BOT_TOKEN"), default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    await setup(dp)
    await dp.start_polling(app)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        sys.exit(0)
