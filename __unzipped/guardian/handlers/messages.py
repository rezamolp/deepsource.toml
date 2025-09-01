from telegram import Update
from telegram.ext import ContextTypes
from services.channel import change_public_link
from utils.validators import normalize_phone
from utils.keyboards import main_menu, otp_keyboard
import logging, uuid

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or '').strip()
    logger = logging.getLogger(__name__)
    logger.info('message_received', extra={
        'event': 'message_received',
        'chat_id': getattr(update.effective_chat, 'id', None),
        'user_id': getattr(update.effective_user, 'id', None),
        'state': dict(context.user_data),
        'action': 'route',
    })
    if text in {"بازگشت", "back", "/back"}:
        context.user_data.clear()
        await update.message.reply_text('بازگشت به منوی اصلی.', reply_markup=main_menu()); return
    if context.user_data.get('waiting_for_channel'):
        base = text.split('/')[-1].lstrip('@')
        context.user_data['waiting_for_channel'] = False
        logger.info('channel_set', extra={'event':'channel_set','base_username':base})
        await update.message.reply_text(f'کانال ثبت شد: @{base}', reply_markup=main_menu()); return
    if context.user_data.get('waiting_for_manual'):
        base = text.split('/')[-1].lstrip('@')
        await change_public_link(0, base)
        context.user_data['waiting_for_manual'] = False
        logger.info('manual_rotation', extra={'event':'manual_rotation','base_username':base})
        await update.message.reply_text(f'لینک تغییر کرد: @{base}', reply_markup=main_menu()); return
    if context.user_data.get('waiting_for_phone'):
        trace_id = str(uuid.uuid4())
        phone = normalize_phone(text)
        if not phone:
            logger.warning('phone_invalid', extra={'event':'phone_invalid','trace_id':trace_id})
            await update.message.reply_text('❌ شماره معتبر نیست. مثال: +989123456789'); return
        context.user_data['waiting_for_phone'] = False
        context.user_data['waiting_for_code'] = True
        context.user_data['phone'] = phone
        logger.info('send_code_requested', extra={'event':'send_code_requested','trace_id':trace_id})
        await update.message.reply_text('📱 شماره ذخیره شد. کد ورود را ارسال کن:', reply_markup=otp_keyboard()); return
    await update.message.reply_text('پیام دریافت شد.', reply_markup=main_menu())
