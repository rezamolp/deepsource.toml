from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 وضعیت ربات", callback_data="status")],
        [InlineKeyboardButton("🔍 بررسی سلامت", callback_data="health_check")],
        [InlineKeyboardButton("📈 آمار چرخش", callback_data="rotation_stats")],
        [InlineKeyboardButton("➕ ثبت کانال", callback_data="set_channel")],
        [InlineKeyboardButton("🔄 تغییر لینک دستی", callback_data="manual_link")],
        [InlineKeyboardButton("➕ افزودن اکانت Telethon", callback_data="add_account")],
        [InlineKeyboardButton("➕ افزودن ادمین", callback_data="add_admin")],
        [InlineKeyboardButton("🛡 ضداسپم فعال/غیرفعال", callback_data="toggle_antispam")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

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
                     InlineKeyboardButton("🔙 بازگشت", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)
