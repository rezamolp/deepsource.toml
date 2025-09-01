from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 وضعیت ضداسپم", callback_data="status")],
        [InlineKeyboardButton("⚙️ تغییر تنظیمات", callback_data="settings"), InlineKeyboardButton("⚙️ تنظیمات کانال‌ها", callback_data="channel_settings")],
        [InlineKeyboardButton("📜 لاگ آخرین رخدادها", callback_data="logs")],
        [InlineKeyboardButton("🚨 تست ضداسپم", callback_data="test_antispam"), InlineKeyboardButton("🎛️ شبیه‌سازی", callback_data="simulate")],
        [InlineKeyboardButton("➕ افزودن اکانت Telethon", callback_data="add_account")],
        [InlineKeyboardButton("➕ افزودن کانال", callback_data="add_channel")],
        [InlineKeyboardButton("➕ افزودن ادمین", callback_data="add_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def channel_settings_menu(channels: list[str]):
    keyboard = []
    for base in channels or []:
        keyboard.append([InlineKeyboardButton(f"⚙️ @{base}", callback_data=f"cs_{base}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def per_channel_settings_menu(base: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Threshold", callback_data=f"csj_{base}")],
        [InlineKeyboardButton("Join Window (s)", callback_data=f"csw_{base}")],
        [InlineKeyboardButton("View Threshold", callback_data=f"csvt_{base}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="channel_settings")],
    ])

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
