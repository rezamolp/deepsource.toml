from telegram import Update
from telegram.ext import ContextTypes
from utils.data import load_data, save_data
from services.telethon_manager import get_status
from utils.keyboards import main_menu

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
    elif query.data == "settings":
        context.user_data["waiting_for_settings"] = True
        await query.edit_message_text("مقادیر جدید تنظیمات را ارسال کن (مثال: join=10, view=50)", reply_markup=main_menu())
    elif query.data == "logs":
        await query.edit_message_text("نمایش 10 رخداد اخیر (stub)", reply_markup=main_menu())
    elif query.data == "test_antispam":
        await query.edit_message_text("✅ تست ضداسپم اجرا شد (stub)", reply_markup=main_menu())
    elif query.data == "add_account":
        context.user_data["waiting_for_phone"] = True
        await query.edit_message_text("شمارهٔ تلفن را بفرست (مثال: +98912...)", reply_markup=main_menu())
    else:
        await query.edit_message_text("دستور ناشناخته.", reply_markup=main_menu())
