import logging
import re
from telegram.ext import ConversationHandler, MessageHandler, CommandHandler, filters
from services import telethon_manager
from utils.validators import normalize_phone

logger = logging.getLogger(__name__)

AWAIT_PHONE, AWAIT_CODE = range(2)

async def start_add_account(update, context):
    user_id = update.effective_user.id
    logger.info(f"event=add_account step=start user_id={user_id}")
    await update.message.reply_text("📞 لطفاً شماره تلفن خود را ارسال کنید (با +98).")
    return AWAIT_PHONE

async def handle_phone(update, context):
    user_id = update.effective_user.id
    phone_raw = update.message.text.strip() if update.message.text else None
    if not phone_raw and update.message.contact:
        phone_raw = update.message.contact.phone_number

    phone = normalize_phone(phone_raw)
    if not phone:
        logger.warning(f"event=add_account step=invalid_phone user_id={user_id} payload={phone_raw}")
        await update.message.reply_text("❌ شماره معتبر نیست. دوباره امتحان کنید.")
        return AWAIT_PHONE

    try:
        await telethon_manager.start_login(phone)
        logger.info(f"event=add_account step=code_sent user_id={user_id} phone={phone}")
        context.user_data['phone'] = phone
        await update.message.reply_text("📩 کد تایید برای شماره ارسال شد. لطفاً کد را وارد کنید.")
        return AWAIT_CODE
    except Exception as e:
        logger.error(f"event=add_account step=send_code_fail user_id={user_id} phone={phone} error={e}", exc_info=True)
        await update.message.reply_text(f"❌ خطا در ارسال کد: {e}")
        return ConversationHandler.END

async def handle_code(update, context):
    user_id = update.effective_user.id
    code = update.message.text.strip()
    phone = context.user_data.get('phone')
    try:
        await telethon_manager.confirm_login(phone, code)
        logger.info(f"event=add_account step=success user_id={user_id} phone={phone}")
        await update.message.reply_text(f"✅ اکانت {phone} با موفقیت ثبت شد.")
    except Exception as e:
        logger.error(f"event=add_account step=code_fail user_id={user_id} phone={phone} error={e}", exc_info=True)
        await update.message.reply_text(f"❌ خطا در ورود: {e}")
    return ConversationHandler.END

def build_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("addaccount", start_add_account)],
        states={
            AWAIT_PHONE: [
                MessageHandler(filters.CONTACT, handle_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
            ],
            AWAIT_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code)],
        },
        fallbacks=[],
    )
