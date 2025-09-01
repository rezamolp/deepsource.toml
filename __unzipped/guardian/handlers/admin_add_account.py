from telegram import Update
from telegram.ext import ContextTypes
from utils.keyboards import main_menu
from utils.validators import normalize_phone

MAX_ATTEMPTS = 3

async def handle_phone_text(message, state):
    phone = normalize_phone((getattr(message, 'text', '') or '').strip())
    if not phone:
        await message.answer("شماره معتبر نیست. مثال: +989123456789")
        attempts = (await state.get_data()).get('attempts', 0) + 1
        await state.update_data(attempts=attempts)
        if attempts >= MAX_ATTEMPTS:
            await message.answer("❌ تلاش‌ها به پایان رسید. بعداً تلاش کن.")
            await state.clear()
        return
    await state.update_data(phone=phone, attempts=0)
    await message.answer("کد ورود را ارسال کنید:")

async def handle_code_text(message, state):
    code = (getattr(message, 'text', '') or '').strip()
    if not code:
        await message.answer("کد نامعتبر است.")
        return
    await state.update_data(code=code)
    await message.answer("اگر رمز دومرحله‌ای داری وارد کن، وگرنه بزن /skip")

async def handle_password_text(message, state):
    password = (getattr(message, 'text', '') or '').strip()
    await state.update_data(password=password)
    await message.answer("اکانت اضافه شد.")
    await state.clear()
