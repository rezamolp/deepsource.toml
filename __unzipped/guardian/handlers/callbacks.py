from telegram import Update
from telegram.ext import ContextTypes
from utils.data import load_data, save_data
from services.telethon_manager import get_status
from utils.keyboards import main_menu, otp_keyboard, back_menu
import logging, uuid

antispam_enabled = True

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    logger = logging.getLogger(__name__)
    logger.info('button_clicked', extra={
        'event':'button_clicked',
        'chat_id': getattr(update.effective_chat,'id',None),
        'user_id': getattr(update.effective_user,'id',None),
        'data': query.data,
        'state': dict(context.user_data)
    })

    if query.data == "status":
        telethon_status = "آماده" if get_status() == "ready" else "تنظیم‌نشده"
        await query.edit_message_text(
            f"""وضعیت:
ضداسپم: {'فعال' if antispam_enabled else 'غیرفعال'}
Telethon: {telethon_status}""", 
            reply_markup=main_menu()
        )
    elif query.data == "settings":
        context.user_data["waiting_for_settings"] = True
        await query.edit_message_text("مقادیر جدید تنظیمات را ارسال کن (مثال: join=10, view=50)", reply_markup=back_menu())
    elif query.data == "logs":
        await query.edit_message_text("نمایش 10 رخداد اخیر (stub)", reply_markup=main_menu())
    elif query.data == "test_antispam":
        await query.edit_message_text("✅ تست ضداسپم اجرا شد (stub)", reply_markup=main_menu())
    elif query.data == "add_account":
        context.user_data["waiting_for_phone"] = True
        context.user_data.pop("otp_code", None)
        await query.edit_message_text("شمارهٔ تلفن را بفرست (مثال: +98912...)", reply_markup=back_menu())
    elif query.data and query.data.startswith("otp_"):
        digit = query.data.split("_",1)[-1]
        buf = context.user_data.get("otp_code", "")
        if len(buf) < 6 and digit.isdigit():
            buf += digit
        context.user_data["otp_code"] = buf
        logger.info('otp_digit_append', extra={'event':'otp_digit_append','len':len(buf)})
        masked = "*"*len(buf)
        try:
            await query.edit_message_text(f"کد: {masked}", reply_markup=otp_keyboard())
        except Exception:
            await query.message.reply_text(f"کد: {masked}", reply_markup=otp_keyboard())
    elif query.data == "otp_confirm":
        code = context.user_data.get("otp_code", "")
        phone = context.user_data.get("phone")
        trace_id = str(uuid.uuid4())
        from services import telethon_manager
        result = {"error":"no_phone"} if not phone else None
        if phone:
            try:
                result = await telethon_manager.confirm_code(phone, code, trace_id=trace_id)
            except Exception as e:
                result = {"error": str(e)}
        ok = bool(result and not result.get("error"))
        logger.info('otp_confirm', extra={'event':'otp_confirm','result':'ok' if ok else 'fail','trace_id':trace_id})
        context.user_data.pop("otp_code", None)
        context.user_data.pop("waiting_for_code", None)
        text = "✅ ورود موفق." if ok else "❌ کد نامعتبر یا خطا در ورود."
        await query.edit_message_text(text, reply_markup=main_menu())
    elif query.data == "back":
        context.user_data.clear()
        await query.edit_message_text("بازگشت به منوی اصلی.", reply_markup=main_menu())
    else:
        await query.edit_message_text("دستور ناشناخته.", reply_markup=main_menu())
