from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from utils.keyboards import main_menu

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "🌸 سلام ادمین عزیز! از منوی زیر استفاده کن:",
        reply_markup=main_menu()
    )
