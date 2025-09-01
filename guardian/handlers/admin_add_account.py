# LEGACY: Aiogram handler, kept for reference only
from aiogram import Router, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from utils.logger import setup_logger

router = Router()
logger = setup_logger()

class AddAccount(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()

@router.message(AddAccount.waiting_for_phone)
async def handle_phone_text(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    if not phone.startswith('+98') and not phone.startswith('0098') and not phone.startswith('09'):
        await message.answer("شماره معتبر نیست. مثال: +989123456789")
        return
    await state.update_data(phone=phone)
    await message.answer("کد ورود را ارسال کنید:")
    await state.set_state(AddAccount.waiting_for_code)

@router.message(AddAccount.waiting_for_code)
async def handle_code_text(message: types.Message, state: FSMContext):
    code = message.text.strip()
    await state.update_data(code=code)
    await message.answer("اگر رمز دومرحله‌ای داری وارد کن، وگرنه بزن /skip")
    await state.set_state(AddAccount.waiting_for_password)

@router.message(AddAccount.waiting_for_password)
async def handle_password_text(message: types.Message, state: FSMContext):
    password = message.text.strip()
    await state.update_data(password=password)
    await message.answer("اکانت اضافه شد.")
    await state.clear()
