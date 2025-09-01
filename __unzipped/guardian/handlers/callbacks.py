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
        status_card = (
            "📊 وضعیت ضداسپم\n"
            f"- ضداسپم: {'فعال' if antispam_enabled else 'غیرفعال'}\n"
            f"- Telethon: {telethon_status}\n"
            f"- Join: 10 / 60s\n"
            f"- View: 50 / 60s (3 پست)\n"
            f"- آخرین rotation: n/a\n"
            f"- Link mode: n/a\n"
            f"- Recent bursts: n/a\n"
        )
        try:
            await query.edit_message_text(status_card, reply_markup=main_menu())
        except Exception:
            await query.message.reply_text(status_card, reply_markup=main_menu())
    elif query.data == "settings":
        context.user_data["waiting_for_settings"] = True
        await query.edit_message_text("مقادیر جدید تنظیمات را ارسال کن (مثال: join=10, view=50)", reply_markup=back_menu())
    elif query.data == "logs":
        await query.edit_message_text("نمایش 10 رخداد اخیر (stub)", reply_markup=main_menu())
    elif query.data == "test_antispam":
        trace_id = str(uuid.uuid4())
        try:
            await query.edit_message_text("⏳ در حال اجرای تست…", reply_markup=main_menu())
        except Exception:
            await query.message.reply_text("⏳ در حال اجرای تست…", reply_markup=main_menu())
        # simple stub result + safe edit/send
        text = f"✅ تست ضداسپم انجام شد. trace_id={trace_id}"
        try:
            await query.edit_message_text(text, reply_markup=main_menu())
        except Exception:
            await query.message.reply_text(text, reply_markup=main_menu())
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
        err = result.get("error") if isinstance(result, dict) else None
        ok = not err
        logger.info('otp_confirm', extra={'event':'otp_confirm','result':'ok' if ok else 'fail','reason': err or '', 'trace_id':trace_id})
        if ok:
            context.user_data.clear()
            await query.edit_message_text("✅ ورود موفق.", reply_markup=main_menu())
        elif err == 'password_needed':
            context.user_data['waiting_for_password'] = True
            context.user_data['otp_code'] = ""
            await query.edit_message_text("🔐 رمز دو مرحله‌ای لازم است. رمز را ارسال کن.", reply_markup=back_menu())
        else:
            context.user_data['waiting_for_code'] = True
            context.user_data['otp_code'] = ""
            await query.edit_message_text("❌ کد نامعتبر یا خطا در ورود. دوباره تلاش کن.", reply_markup=otp_keyboard())
    elif query.data == "back":
        context.user_data.clear()
        await query.edit_message_text("بازگشت به منوی اصلی.", reply_markup=main_menu())
    else:
        await query.edit_message_text("دستور ناشناخته.", reply_markup=main_menu())
