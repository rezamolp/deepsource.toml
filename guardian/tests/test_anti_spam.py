from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

from aiogram import Bot

from guardian.anti_spam import AntiSpamService, Thresholds
from guardian.db.base import create_session_factory
from guardian.db.models import Base
from guardian.db.repo import Repository
from guardian.rotation import LinkRotationManager


class DummyRotation:
    async def rotate(self, chat_id: int, base: str, max_suffix: int):
        return ("https://t.me/guardian", "username")


async def test_join_burst_triggers_rotation(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    SessionLocal, engine = create_session_factory(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    repo = Repository(SessionLocal())

    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()
    rotation = DummyRotation()
    thresholds = Thresholds(join_threshold=10, join_window_seconds=60, view_threshold=50, view_window_seconds=60)
    svc = AntiSpamService(repo, bot, rotation, chat_id=-1001, admin_id=1, admin_fallback_chat_id=None, thresholds=thresholds)

    await svc.handle_join(12)
    # At least one rotation log should exist
    assert len(repo.last_rotations(10)) >= 1
