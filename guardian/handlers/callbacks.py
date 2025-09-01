from telegram import Update
from telegram.ext import ContextTypes
from utils.data import load_data, save_data
from services.telethon_manager import get_status
from handlers.commands import main_menu

antispam_enabled = True

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()

    if query.data == "status":
        telethon_status = "آماده" if get_status() == "ready" else "تنظیم‌نشده"
        await query.edit_message_text(
            f"""وضعیت:
ضداسپم: {'فعال' if antispam_enabled else 'غیرفعال'}
Telethon: {telethon_status}""", 
            reply_markup=main_menu()
        )
    elif query.data == "set_channel":
        context.user_data["waiting_for_channel"] = True
        await query.edit_message_text("نام کاربری کانال (@name یا t.me/...) را بفرست.", reply_markup=main_menu())
    elif query.data == "manual_link":
        context.user_data["waiting_for_manual"] = True
        await query.edit_message_text("نام کاربری جهت چرخش لینک را بفرست.", reply_markup=main_menu())
    elif query.data == "add_account":
        context.user_data["waiting_for_phone"] = True
        await query.edit_message_text("شمارهٔ تلفن را بفرست (مثال: +98912...)", reply_markup=main_menu())
    else:
        await query.edit_message_text("دستور ناشناخته.", reply_markup=main_menu())
