from telegram import Update
from telegram.ext import ContextTypes
from utils.keyboards import main_menu
from utils.validators import normalize_phone

MAX_ATTEMPTS = 3

async def handle_phone_text(message, state):
    phone = normalize_phone((getattr(message, 'text', '') or '').strip())
    if not phone:
        await message.answer("شماره معتبر نیست. مثال: +989123456789")
        # FSM compatibility shim
        attempts = 0
        try:
            data = await state.get_data()
            attempts = int(data.get('attempts', 0)) + 1
            await state.update_data(attempts=attempts)
        except Exception:
            prev = getattr(state, 'attempts', 0)
            attempts = int(prev) + 1
            try:
                setattr(state, 'attempts', attempts)
            except Exception:
                pass
        if attempts >= MAX_ATTEMPTS:
            await message.answer("❌ تلاش‌ها به پایان رسید. بعداً تلاش کن.")
            try:
                await state.clear()
            except Exception:
                pass
        return
    try:
        await state.update_data(phone=phone, attempts=0)
    except Exception:
        try:
            setattr(state, 'phone', phone)
            setattr(state, 'attempts', 0)
        except Exception:
            pass
    await message.answer("کد ورود را ارسال کنید:")

async def handle_code_text(message, state):
    code = (getattr(message, 'text', '') or '').strip()
    if not code:
        await message.answer("کد نامعتبر است.")
        return
    try:
        await state.update_data(code=code)
    except Exception:
        try:
            setattr(state, 'code', code)
        except Exception:
            pass
    await message.answer("اگر رمز دومرحله‌ای داری وارد کن، وگرنه بزن /skip")

async def handle_password_text(message, state):
    password = (getattr(message, 'text', '') or '').strip()
    try:
        await state.update_data(password=password)
    except Exception:
        try:
            setattr(state, 'password', password)
        except Exception:
            pass
    await message.answer("اکانت اضافه شد.")
    try:
        await state.clear()
    except Exception:
        pass
