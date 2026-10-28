from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Allow importing packages/mtproto without install
_ROOT = Path(__file__).resolve().parents[3]
_PKG = _ROOT / "packages" / "mtproto"
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from .config import get_settings
from .db import init_db
from .handlers import setup_routers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("mtproto_shop")


async def on_startup(bot: Bot) -> None:
    settings = get_settings()
    await init_db()
    me = await bot.get_me()
    log.info("bot online @%s id=%s", me.username, me.id)
    if settings.webhook_url:
        url = settings.webhook_url.rstrip("/") + settings.webhook_path
        await bot.set_webhook(url, secret_token=settings.webhook_secret or None)
        log.info("webhook set")
    else:
        await bot.delete_webhook(drop_pending_updates=False)


async def on_shutdown(bot: Bot) -> None:
    settings = get_settings()
    if settings.webhook_url:
        await bot.delete_webhook()


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(setup_routers())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    return dp


async def run_polling() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN is required (see .env.example)")
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()
    await dp.start_polling(bot)


def run_webhook() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN is required")
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()
    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret or None,
    ).register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=8080)


def main() -> None:
    settings = get_settings()
    if settings.webhook_url:
        run_webhook()
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
