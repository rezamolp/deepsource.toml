from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot
from telethon import TelegramClient

from .anti_spam import AntiSpamService, Thresholds
from .bot import AdminBot
from .config import load_settings
from .db.base import create_session_factory
from .db.models import Base  # ensure models loaded
from .db.repo import Repository
from .health import run_health_server
from .logging import setup_logging
from .rotation import LinkRotationManager
from .telethon_login import TelethonAccountManager
from .monitors import ViewMonitor, JoinPoller


async def main_async() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    # Ensure sessions directory exists
    os.makedirs("sessions", exist_ok=True)

    # DB
    SessionLocal, engine = create_session_factory(settings.database_url)
    # Create tables at startup if not exist
    Base.metadata.create_all(engine)
    repo = Repository(SessionLocal())
    # Persist rotation settings for runtime edits via admin bot
    repo.set_setting("rotation_base", settings.rotation_base)
    repo.set_setting("rotation_suffix_max", str(settings.rotation_suffix_max))
    repo.set_setting("join_threshold", str(settings.join_threshold))
    repo.set_setting("join_window_seconds", str(settings.join_window_seconds))
    repo.set_setting("view_threshold", str(settings.view_threshold))

    # Bots/Clients
    bot = Bot(token=settings.bot_token)
    telethon_client = TelegramClient("sessions/guardian", settings.api_id, settings.api_hash)
    await telethon_client.connect()

    rotation = LinkRotationManager(settings.api_id, settings.api_hash)
    telethon_mgr = TelethonAccountManager(settings.api_id, settings.api_hash)

    thresholds = Thresholds(
        join_threshold=settings.join_threshold,
        join_window_seconds=settings.join_window_seconds,
        view_threshold=settings.view_threshold,
        view_window_seconds=settings.view_window_seconds,
    )
    anti_spam = AntiSpamService(
        repo=repo,
        bot=bot,
        rotation=rotation,
        chat_id=settings.target_chat_id,
        admin_id=settings.admin_id,
        admin_fallback_chat_id=settings.admin_fallback_chat_id,
        thresholds=thresholds,
    )

    # Monitors
    view_monitor = ViewMonitor(telethon=telethon_client, anti_spam=anti_spam, poll_seconds=settings.view_monitor_poll_seconds)
    join_poller = JoinPoller(telethon=telethon_client, anti_spam=anti_spam)

    # Admin bot
    admin_bot = AdminBot(bot=bot, repo=repo, admin_id=settings.admin_id, telethon_mgr=telethon_mgr, anti_spam=anti_spam)

    # Tasks
    tasks = [
        asyncio.create_task(admin_bot.run(), name="admin-bot"),
        asyncio.create_task(view_monitor.start(), name="view-monitor"),
        asyncio.create_task(join_poller.start(), name="join-poller"),
        asyncio.create_task(run_health_server(settings.health_host, settings.health_port), name="health"),
    ]
    await asyncio.gather(*tasks)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
