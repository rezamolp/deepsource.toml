from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 وضعیت ضداسپم", callback_data="status")],
        [InlineKeyboardButton("⚙️ تغییر تنظیمات", callback_data="settings")],
        [InlineKeyboardButton("📜 لاگ آخرین رخدادها", callback_data="logs")],
        [InlineKeyboardButton("🚨 تست ضداسپم", callback_data="test_antispam"), InlineKeyboardButton("🎛️ شبیه‌سازی", callback_data="simulate")],
        [InlineKeyboardButton("➕ افزودن اکانت Telethon", callback_data="add_account")],
        [InlineKeyboardButton("➕ افزودن کانال", callback_data="add_channel")],
        [InlineKeyboardButton("➕ افزودن ادمین", callback_data="add_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]])

def otp_keyboard():
    keyboard = []
    row = []
    for i in range(10):
        row.append(InlineKeyboardButton(str(i), callback_data=f"otp_{i}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("✅ تایید", callback_data="otp_confirm"),
                     InlineKeyboardButton("⌫ حذف", callback_data="otp_backspace"),
                     InlineKeyboardButton("✉️ ارسال کد به‌صورت پیام", callback_data="otp_text"),
                     InlineKeyboardButton("🔙 بازگشت", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)
