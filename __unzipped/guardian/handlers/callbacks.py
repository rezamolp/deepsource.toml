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
        data = load_data() or {}
        channels = data.get('channels', [])
        success = int(data.get('link_changes_success', 0))
        fail = int(data.get('link_changes_fail', 0))
        attacks = int(data.get('attacks', 0))
        tele_phone = data.get('telethon_phone', 'n/a')
        last_link = data.get('last_rotation_link', 'n/a')
        session_ok = data.get('session_status', 'n/a')
        status_card = (
            "📊 وضعیت ضداسپم\n"
            f"- ضداسپم: {'فعال' if antispam_enabled else 'غیرفعال'}\n"
            f"- Telethon: {telethon_status} (phone={tele_phone}, session={session_ok})\n"
            f"- Join threshold/window: 10 / 60s\n"
            f"- View threshold/window: 50 / 60s (3 پست)\n"
            f"- کانال‌ها: {len(channels)}\n"
            f"- آخرین لینک/rotation: {last_link}\n"
            f"- link_changes: ok={success} / fail={fail}\n"
            f"- attacks: {attacks}\n"
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
        chat_id = context.bot_data.get('channel_id') or getattr(update.effective_chat, 'id', 0)
        base_username = context.bot_data.get('base_username') or 'guardian'
        # simulate direct rotation
        from services.link_rotator import rotate_username
        # Prechecks: session, channel, permissions (basic)
        data = load_data() or {}
        session_ok = data.get('session_status') == 'ok'
        channels = data.get('channels', [])
        if not session_ok:
            msg = "⛔ سشن Telethon فعال نیست. ابتدا ورود را کامل کن."
            try:
                await query.edit_message_text(msg, reply_markup=main_menu())
            except Exception:
                await query.message.reply_text(msg, reply_markup=main_menu())
            return
        if not channels:
            msg = "⛔ هیچ کانالی ثبت نشده. از گزینهٔ افزودن کانال استفاده کن."
            try:
                await query.edit_message_text(msg, reply_markup=main_menu())
            except Exception:
                await query.message.reply_text(msg, reply_markup=main_menu())
            return
        try:
            await query.edit_message_text("⏳ تست ضداسپم: تلاش برای چرخش…", reply_markup=main_menu())
        except Exception:
            await query.message.reply_text("⏳ تست ضداسپم: تلاش برای چرخش…", reply_markup=main_menu())
        result = await rotate_username(context, chat_id, base_username, trace_id=trace_id)
        # telemetry: increment attacks
        try:
            d = load_data() or {}
            d['attacks'] = int(d.get('attacks', 0)) + 1
            save_data(d)
        except Exception:
            pass
        if result.get('ok'):
            msg = f"✅ چرخش موفق. trace_id={trace_id}"
        else:
            msg = f"❌ چرخش ناموفق: {result.get('error','unknown')}. trace_id={trace_id}"
        try:
            await query.edit_message_text(msg, reply_markup=main_menu())
        except Exception:
            await query.message.reply_text(msg, reply_markup=main_menu())
    elif query.data == "add_account":
        context.user_data["waiting_for_phone"] = True
        context.user_data.pop("otp_code", None)
        await query.edit_message_text("شمارهٔ تلفن را بفرست (مثال: +98912...)", reply_markup=back_menu())
    elif query.data == "add_channel":
        context.user_data["waiting_for_channel"] = True
        await query.edit_message_text("نام کاربری کانال (@name یا t.me/...) را بفرست.", reply_markup=back_menu())
    elif query.data == "add_admin":
        context.user_data["waiting_for_admin"] = True
        await query.edit_message_text("شناسهٔ عددی یا @username ادمین جدید را بفرست.", reply_markup=back_menu())
    elif query.data == "otp_text":
        context.user_data["waiting_for_code"] = True
        await query.edit_message_text("کد را به صورت پیام متنی ارسال کن (۴ تا ۸ رقم)", reply_markup=otp_keyboard())
    elif query.data and query.data.startswith("otp_"):
        digit = query.data.split("_",1)[-1]
        buf = context.user_data.get("otp_code", "")
        if len(buf) < 6 and digit.isdigit():
            buf += digit
        context.user_data["otp_code"] = buf
        logger.info('otp_digit_append', extra={'event':'otp_digit_append','len':len(buf)})
        masked = buf  # نمایش مستقیم ارقام طبق درخواست، ولی لاگ فقط length دارد
        try:
            await query.edit_message_text(f"کد: {masked}", reply_markup=otp_keyboard())
        except Exception:
            await query.message.reply_text(f"کد: {masked}", reply_markup=otp_keyboard())
    elif query.data == "otp_confirm":
        code = context.user_data.get("otp_code", "")
        phone = context.user_data.get("phone")
        trace_id = context.user_data.get("trace_id") or str(uuid.uuid4())
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
            try:
                await query.edit_message_text("✅ ورود موفق.", reply_markup=main_menu())
            except Exception:
                await query.message.reply_text("✅ ورود موفق.", reply_markup=main_menu())
        elif err == 'password_needed':
            context.user_data['waiting_for_password'] = True
            context.user_data['otp_code'] = ""
            try:
                await query.edit_message_text("🔐 رمز دو مرحله‌ای لازم است. رمز را ارسال کن.", reply_markup=back_menu())
            except Exception:
                await query.message.reply_text("🔐 رمز دو مرحله‌ای لازم است. رمز را ارسال کن.", reply_markup=back_menu())
        else:
            context.user_data['waiting_for_code'] = True
            context.user_data['otp_code'] = ""
            try:
                await query.edit_message_text("❌ کد نامعتبر یا خطا در ورود. دوباره تلاش کن.", reply_markup=otp_keyboard())
            except Exception:
                await query.message.reply_text("❌ کد نامعتبر یا خطا در ورود. دوباره تلاش کن.", reply_markup=otp_keyboard())
    elif query.data == "back":
        context.user_data.clear()
        await query.edit_message_text("بازگشت به منوی اصلی.", reply_markup=main_menu())
    else:
        await query.edit_message_text("دستور ناشناخته.", reply_markup=main_menu())
