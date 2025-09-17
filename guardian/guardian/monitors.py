from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from aiogram import Bot
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest

from .anti_spam import AntiSpamService
from .db.repo import Repository


logger = logging.getLogger(__name__)


class JoinMonitor:
    def __init__(self, bot: Bot, anti_spam: AntiSpamService, chat_id: int) -> None:
        self.bot = bot
        self.anti_spam = anti_spam
        self.chat_id = chat_id

    async def on_member_join(self, count: int) -> None:
        await self.anti_spam.handle_join(count)


class ViewMonitor:
    def __init__(self, telethon: TelegramClient, anti_spam: AntiSpamService, chat_id: int, poll_seconds: int = 10) -> None:
        self.telethon = telethon
        self.anti_spam = anti_spam
        self.chat_id = chat_id
        self.poll_seconds = poll_seconds
        self._last_views: List[int] = []

    async def start(self) -> None:
        while True:
            try:
                history = await self.telethon(GetHistoryRequest(
                    peer=self.chat_id,
                    limit=3,
                    offset_date=None,
                    offset_id=0,
                    max_id=0,
                    min_id=0,
                    add_offset=0,
                    hash=0,
                ))
                curr_views = []
                for m in history.messages:
                    v = getattr(m, "views", None)
                    if isinstance(v, int):
                        curr_views.append(v)
                curr_views = curr_views[:3]
                if len(curr_views) > 0 and len(self._last_views) == len(curr_views):
                    growth = 0
                    oscillation = False
                    for prev, curr in zip(self._last_views, curr_views):
                        if curr < prev:
                            oscillation = True
                        growth += max(0, curr - prev)
                    if oscillation:
                        # Treat as suspicious
                        growth = max(growth, 50)
                    if growth > 0:
                        await self.anti_spam.handle_view_growth(growth)
                self._last_views = curr_views
            except Exception:
                pass
            await asyncio.sleep(self.poll_seconds)


class JoinPoller:
    def __init__(self, telethon: TelegramClient, anti_spam: AntiSpamService, chat_id: int, poll_seconds: int = 5) -> None:
        self.telethon = telethon
        self.anti_spam = anti_spam
        self.chat_id = chat_id
        self.poll_seconds = poll_seconds
        self._last_count: Optional[int] = None

    async def start(self) -> None:
        while True:
            try:
                full = await self.telethon(GetFullChannelRequest(channel=self.chat_id))
                full_chat = full.full_chat
                count = getattr(full_chat, "participants_count", None) or getattr(full_chat, "subscribers", None)
                if isinstance(count, int):
                    if self._last_count is not None:
                        delta = count - self._last_count
                        if delta >= 1:
                            await self.anti_spam.handle_join(delta)
                    self._last_count = count
            except Exception:
                pass
            await asyncio.sleep(self.poll_seconds)
