from telegram import Update
from telegram.ext import ContextTypes
from services.channel import change_public_link
from utils.validators import normalize_phone
from handlers.callbacks import main_menu

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or '').strip()
    if context.user_data.get('waiting_for_channel'):
        base = text.split('/')[-1].lstrip('@')
        context.user_data['waiting_for_channel'] = False
        await update.message.reply_text(f'کانال ثبت شد: @{base}', reply_markup=main_menu()); return
    if context.user_data.get('waiting_for_manual'):
        base = text.split('/')[-1].lstrip('@')
        await change_public_link(0, base)
        context.user_data['waiting_for_manual'] = False
        await update.message.reply_text(f'لینک تغییر کرد: @{base}', reply_markup=main_menu()); return
    if context.user_data.get('waiting_for_phone'):
        phone = normalize_phone(text)
        if not phone:
            await update.message.reply_text('❌ شماره معتبر نیست. مثال: +989123456789'); return
        context.user_data['waiting_for_phone'] = False
        await update.message.reply_text('📱 شماره ذخیره شد.', reply_markup=main_menu()); return
    await update.message.reply_text('پیام دریافت شد.', reply_markup=main_menu())
