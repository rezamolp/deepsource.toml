from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
import time
from typing import Optional

from aiogram import Bot

from .db.repo import Repository
from .rotation import LinkRotationManager
from .utils import ConcurrencyGuard, generate_trace_id


logger = logging.getLogger(__name__)


@dataclass
class Thresholds:
    join_threshold: int
    join_window_seconds: int
    view_threshold: int
    view_window_seconds: int


class AntiSpamService:
    def __init__(
        self,
        repo: Repository,
        bot: Bot,
        rotation: LinkRotationManager,
        chat_id: int,
        admin_id: int,
        admin_fallback_chat_id: Optional[int],
        thresholds: Thresholds,
    ) -> None:
        self.repo = repo
        self.bot = bot
        self.rotation = rotation
        self.chat_id = chat_id
        self.admin_id = admin_id
        self.admin_fallback_chat_id = admin_fallback_chat_id
        self.thresholds = thresholds
        self.guard = ConcurrencyGuard()
        self._last_rotation_at: float = 0.0

    async def _notify_admin(self, text: str) -> None:
        try:
            await self.bot.send_message(self.admin_id, text)
        except Exception:
            if self.admin_fallback_chat_id:
                try:
                    await self.bot.send_message(self.admin_fallback_chat_id, text)
                except Exception:
                    pass

    async def _rotate_link(self, reason: str, trace_id: str, base: str, max_suffix: int) -> Optional[str]:
        try:
            link, mode = await self.rotation.rotate(self.chat_id, base, max_suffix)
            await self._notify_admin(f"🔄 لینک کانال با موفقیت تغییر یافت.\nلینک جدید: {link}\ntrace_id={trace_id}")
            self.repo.add_rotation_log(self.chat_id, result="ok", reason=reason, new_link=link, trace_id=trace_id)
            return link
        except Exception as ex:
            self.repo.add_rotation_log(self.chat_id, result="fail", reason=reason, new_link=None, trace_id=trace_id)
            await self._notify_admin(f"⏳ خطا در چرخش لینک: {ex}\ntrace_id={trace_id}")
            return None

    def get_current_chat_id(self) -> Optional[int]:
        # Prefer dynamic value from settings if present
        value = self.repo.get_setting("target_chat_id")
        if value and value.strip().lstrip("-").isdigit():
            try:
                return int(value)
            except ValueError:
                pass
        return self.chat_id

    async def handle_join(self, count: int) -> None:
        chat_id = self.get_current_chat_id()
        if chat_id is None:
            return
        trace_id = generate_trace_id()
        self.repo.prune_events(chat_id, "join", self.thresholds.join_window_seconds)
        self.repo.add_event(chat_id, "join", count, trace_id)
        total = self.repo.window_count(chat_id, "join", self.thresholds.join_window_seconds)

        # Burst if total >= threshold or "exactly threshold at once"
        if total >= self.thresholds.join_threshold or count >= self.thresholds.join_threshold:
            # Concurrency guard 2s simulated by one lock; join and view share same guard key 'rotation'
            async with self.guard.acquire(chat_id, "rotation"):
                now = time.monotonic()
                if now - self._last_rotation_at < 2.0:
                    # Suppress duplicate rotation within 2 seconds window
                    return
                msg = (
                    f"🚨 [Join-Burst Detected]\n"
                    f"تعداد: {total}\n"
                    f"پنجره: {self.thresholds.join_window_seconds} ثانیه\n"
                    f"trace_id={trace_id}"
                )
                await self._notify_admin(msg)
                self._last_rotation_at = now
                await self._rotate_link(
                    reason="join_burst",
                    trace_id=trace_id,
                    base=self.repo.get_setting("rotation_base", default="guardian") or "guardian",
                    max_suffix=int(self.repo.get_setting("rotation_suffix_max", default="100") or 100),
                )

    async def handle_view_growth(self, growth: int) -> None:
        chat_id = self.get_current_chat_id()
        if chat_id is None:
            return
        trace_id = generate_trace_id()
        self.repo.prune_events(chat_id, "view", self.thresholds.view_window_seconds)
        self.repo.add_event(chat_id, "view", growth, trace_id)
        total = self.repo.window_count(chat_id, "view", self.thresholds.view_window_seconds)
        if total >= self.thresholds.view_threshold or growth >= self.thresholds.view_threshold:
            async with self.guard.acquire(chat_id, "rotation"):
                now = time.monotonic()
                if now - self._last_rotation_at < 2.0:
                    return
                msg = (
                    f"🚨 [View-Burst Detected]\n"
                    f"پست‌های پایش: 3\n"
                    f"رشد: +{growth}\n"
                    f"trace_id={trace_id}"
                )
                await self._notify_admin(msg)
                self._last_rotation_at = now
                await self._rotate_link(
                    reason="view_burst",
                    trace_id=trace_id,
                    base=self.repo.get_setting("rotation_base", default="guardian") or "guardian",
                    max_suffix=int(self.repo.get_setting("rotation_suffix_max", default="100") or 100),
                )

    async def simulate_test(self) -> None:
        trace_id = "test123"
        async with self.guard.acquire(self.chat_id, "rotation"):
            now = time.monotonic()
            self._last_rotation_at = now
            await self._rotate_link(
                reason="test",
                trace_id=trace_id,
                base=self.repo.get_setting("rotation_base", default="guardian") or "guardian",
                max_suffix=int(self.repo.get_setting("rotation_suffix_max", default="100") or 100),
            )
