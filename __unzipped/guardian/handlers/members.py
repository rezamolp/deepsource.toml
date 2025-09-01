from telegram import Update
from telegram.ext import ContextTypes
from services.antispam import check_new_member
from services import channel

async def member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_member and update.chat_member.new_chat_member:
        status = update.chat_member.new_chat_member.status
        if status == "member":
            channel_id = context.bot_data.get('channel_id')
            base_username = context.bot_data.get('base_username')
            if channel_id and base_username:
                await check_new_member(context, channel_id, base_username)
