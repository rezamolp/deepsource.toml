from __future__ import annotations

import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from .db.repo import Repository
from .telethon_login import TelethonAccountManager
from .anti_spam import AntiSpamService
from .utils import mask


logger = logging.getLogger(__name__)


class TelethonLoginFSM(StatesGroup):
    phone = State()
    code = State()
    password = State()


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 وضعیت ضداسپم", callback_data="status")],
        [InlineKeyboardButton(text="⚙️ تغییر تنظیمات", callback_data="settings")],
        [InlineKeyboardButton(text="📜 لاگ", callback_data="logs")],
        [InlineKeyboardButton(text="🚨 تست ضداسپم", callback_data="test")],
        [InlineKeyboardButton(text="➕ افزودن اکانت Telethon", callback_data="telethon_add")],
    ])


def settings_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Join Threshold", callback_data="set_join_threshold")],
        [InlineKeyboardButton(text="Join Window", callback_data="set_join_window")],
        [InlineKeyboardButton(text="View Threshold", callback_data="set_view_threshold")],
        [InlineKeyboardButton(text="Target Chat ID", callback_data="set_target_chat")],
        [InlineKeyboardButton(text="بازگشت", callback_data="back_home")],
    ])


class AdminBot:
    def __init__(self, bot: Bot, repo: Repository, admin_id: int, telethon_mgr: TelethonAccountManager, anti_spam: Optional[AntiSpamService] = None) -> None:
        self.bot = bot
        self.repo = repo
        self.admin_id = admin_id
        self.telethon_mgr = telethon_mgr
        self.anti_spam = anti_spam
        self.dp = Dispatcher(storage=MemoryStorage())
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.dp.message(CommandStart())
        async def start(message: Message) -> None:
            if message.from_user and message.from_user.id != self.admin_id:
                return
            await message.answer("به گاردین خوش آمدید.", reply_markup=admin_menu_kb())

        @self.dp.callback_query(F.data == "status")
        async def status(cb: CallbackQuery) -> None:
            join_threshold = int(self.repo.get_setting("join_threshold", "10") or 10)
            join_window = int(self.repo.get_setting("join_window_seconds", "60") or 60)
            view_threshold = int(self.repo.get_setting("view_threshold", "50") or 50)
            rotation_base = self.repo.get_setting("rotation_base", "guardian") or "guardian"
            rotation_suffix_max = int(self.repo.get_setting("rotation_suffix_max", "100") or 100)
            last_rot = self.repo.last_rotations(1)
            last_text = "—"
            if last_rot:
                r = last_rot[0]
                last_text = f"{r.ts} | {r.reason} | {r.result} | {r.new_link or '—'} | {r.trace_id or '—'}"
            await cb.message.edit_text(
                (
                    "📊 وضعیت ضداسپم\n"
                    f"Join: {join_threshold} / {join_window}s\n"
                    f"View: {view_threshold} / 60s (3 پست آخر)\n"
                    f"base: {rotation_base}, max: {rotation_suffix_max}\n"
                    f"آخرین رخداد: {last_text}"
                ), reply_markup=admin_menu_kb()
            )
            await cb.answer()

        @self.dp.callback_query(F.data == "settings")
        async def settings(cb: CallbackQuery) -> None:
            await cb.message.edit_text("⚙️ تنظیمات را انتخاب کنید:", reply_markup=settings_kb())
            await cb.answer()

        async def _prompt_int(cb: CallbackQuery, key: str, title: str) -> None:
            await cb.message.edit_text(f"{title} را وارد کنید (≥1):")
            self.repo.set_setting("_await_key", key)

        @self.dp.callback_query(F.data == "set_join_threshold")
        async def set_jt(cb: CallbackQuery) -> None:
            await _prompt_int(cb, "join_threshold", "Join Threshold")
            await cb.answer()

        @self.dp.callback_query(F.data == "set_join_window")
        async def set_jw(cb: CallbackQuery) -> None:
            await _prompt_int(cb, "join_window_seconds", "Join Window")
            await cb.answer()

        @self.dp.callback_query(F.data == "set_view_threshold")
        async def set_vt(cb: CallbackQuery) -> None:
            await _prompt_int(cb, "view_threshold", "View Threshold")
            await cb.answer()

        @self.dp.callback_query(F.data == "set_target_chat")
        async def set_target_chat(cb: CallbackQuery) -> None:
            await _prompt_int(cb, "target_chat_id", "Target Chat ID")
            await cb.answer()

        @self.dp.callback_query(F.data == "back_home")
        async def back_home(cb: CallbackQuery) -> None:
            await cb.message.edit_text("منوی اصلی:", reply_markup=admin_menu_kb())
            await cb.answer()

        @self.dp.message()
        async def any_message(message: Message) -> None:
            if message.from_user and message.from_user.id != self.admin_id:
                return
            awaiting_key = self.repo.get_setting("_await_key")
            if awaiting_key:
                text = (message.text or "").strip()
                if not text.isdigit() or int(text) < 1:
                    await message.answer("❌ مقدار باید بزرگ‌تر از صفر باشد.")
                    return
                self.repo.set_setting(awaiting_key, text)
                self.repo.set_setting("_await_key", "")
                await message.answer("✅ ذخیره شد.", reply_markup=admin_menu_kb())

        @self.dp.callback_query(F.data == "logs")
        async def logs(cb: CallbackQuery) -> None:
            events = self.repo.last_events(10)
            rotations = self.repo.last_rotations(5)
            lines = ["📜 رویدادها:"]
            for e in events:
                lines.append(f"{e.ts} | {e.kind} | +{e.count} | {e.trace_id or '—'}")
            lines.append("\n🔄 چرخش‌ها:")
            for r in rotations:
                lines.append(f"{r.ts} | {r.reason} | {r.result} | {r.new_link or '—'} | {r.trace_id or '—'}")
            await cb.message.edit_text("\n".join(lines), reply_markup=admin_menu_kb())
            await cb.answer()

        @self.dp.callback_query(F.data == "test")
        async def test(cb: CallbackQuery) -> None:
            if self.anti_spam:
                await self.anti_spam.simulate_test()
            await cb.message.answer("✅ تست موفق: لینک کانال تغییر کرد.\ntrace_id=test123")
            await cb.answer()

        @self.dp.callback_query(F.data == "telethon_add")
        async def telethon_add(cb: CallbackQuery, state: FSMContext) -> None:
            await state.set_state(TelethonLoginFSM.phone)
            await state.update_data(attempts=0, cooldown_until=0)
            await cb.message.answer("شماره تلفن اکانت Telethon را وارد کنید:")
            await cb.answer()

        @self.dp.message(TelethonLoginFSM.phone)
        async def telethon_get_phone(message: Message, state: FSMContext) -> None:
            if message.from_user and message.from_user.id != self.admin_id:
                return
            phone = (message.text or "").strip()
            await state.update_data(phone=phone)
            res = await self.telethon_mgr.send_code(phone)
            if not res.ok:
                await message.answer("❌ خطا در ارسال کد. دوباره تلاش کنید.")
                return
            await state.set_state(TelethonLoginFSM.code)
            await message.answer("کد تایید را وارد کنید:")

        @self.dp.message(TelethonLoginFSM.code)
        async def telethon_get_code(message: Message, state: FSMContext) -> None:
            if message.from_user and message.from_user.id != self.admin_id:
                return
            data = await state.get_data()
            phone = data.get("phone", "")
            code = (message.text or "").strip()
            attempts = int(data.get("attempts", 0))
            cooldown_until = float(data.get("cooldown_until", 0))
            now = asyncio.get_event_loop().time()
            if cooldown_until and now < cooldown_until:
                await message.answer("⏳ مسیر قفل است. لطفاً بعداً تلاش کنید.")
                return
            if attempts >= 3:
                await message.answer("⏳ مسیر قفل شد. لطفا 60 ثانیه منتظر بمانید.")
                return
            res = await self.telethon_mgr.sign_in(phone, code)
            if res.ok:
                await state.clear()
                await message.answer("✅ اکانت جدید اضافه شد.")
                return
            if res.reason == "2fa_needed":
                await state.set_state(TelethonLoginFSM.password)
                await state.update_data(attempts=attempts, cooldown_until=cooldown_until)
                await message.answer("رمز 2FA را وارد کنید:")
                return
            attempts += 1
            await state.update_data(attempts=attempts)
            if attempts >= 3:
                await state.update_data(cooldown_until=now + 60)
                await message.answer("⏳ سه بار اشتباه. مسیر 60 ثانیه قفل شد.")
            else:
                await message.answer("❌ کد نامعتبر. دوباره تلاش کنید.")

        @self.dp.message(TelethonLoginFSM.password)
        async def telethon_get_password(message: Message, state: FSMContext) -> None:
            if message.from_user and message.from_user.id != self.admin_id:
                return
            data = await state.get_data()
            phone = data.get("phone", "")
            password = (message.text or "").strip()
            attempts = int(data.get("attempts", 0))
            cooldown_until = float(data.get("cooldown_until", 0))
            now = asyncio.get_event_loop().time()
            if cooldown_until and now < cooldown_until:
                await message.answer("⏳ مسیر قفل است. لطفاً بعداً تلاش کنید.")
                return
            if attempts >= 3:
                await message.answer("⏳ مسیر قفل شد. لطفا 60 ثانیه منتظر بمانید.")
                return
            res = await self.telethon_mgr.sign_in(phone, code="00000", password=password)
            if res.ok:
                await state.clear()
                await message.answer("✅ اکانت جدید اضافه شد.")
                return
            attempts += 1
            await state.update_data(attempts=attempts)
            if attempts >= 3:
                await state.update_data(cooldown_until=now + 60)
                await message.answer("⏳ سه بار اشتباه. مسیر 60 ثانیه قفل شد.")
            else:
                await message.answer("❌ رمز 2FA نامعتبر. دوباره تلاش کنید.")

    async def run(self) -> None:
        await self.dp.start_polling(self.bot)
