from telegram import Update
from telegram.ext import ContextTypes
from services.channel import change_public_link, resolve_channel_from_input, get_rotation_status
from services.telethon_manager import get_status
from utils.validators import normalize_phone
from handlers.callbacks import main_menu
import logging

logger = logging.getLogger(__name__)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or '').strip()
    
    if context.user_data.get('waiting_for_channel'):
        # Handle channel registration
        await _handle_channel_registration(update, context, text)
        return
        
    if context.user_data.get('waiting_for_manual'):
        # Handle manual link rotation
        await _handle_manual_link_rotation(update, context, text)
        return
        
    if context.user_data.get('waiting_for_phone'):
        # Handle phone number input
        await _handle_phone_input(update, context, text)
        return
        
    await update.message.reply_text('پیام دریافت شد.', reply_markup=main_menu())

async def _handle_channel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle channel registration with health matrix"""
    try:
        # Clean channel input
        base = text.split('/')[-1].lstrip('@')
        context.user_data['waiting_for_channel'] = False
        
        # Show health matrix before proceeding
        health_matrix = await _get_health_matrix(base)
        
        status_message = f"""🔍 **ماتریس سلامت کانال:**
        
📡 **کانال:** @{base}
✅ **Telethon:** {health_matrix['telethon_status']}
👑 **ادمین:** {health_matrix['is_admin']}
🔧 **مجوز تغییر:** {health_matrix['can_change_info']}
👥 **مجوز مشاهده:** {health_matrix['can_view_participants']}
📊 **وضعیت:** {health_matrix['status']}

{health_matrix['message']}"""
        
        await update.message.reply_text(status_message, reply_markup=main_menu())
        
        # Store channel info for future use
        context.user_data['registered_channel'] = base
        context.user_data['channel_health'] = health_matrix
        
    except Exception as e:
        logger.error("channel_registration_failed", extra={
            "input": text,
            "error": str(e)
        })
        await update.message.reply_text(
            f'❌ خطا در ثبت کانال: {str(e)}', 
            reply_markup=main_menu()
        )

async def _handle_manual_link_rotation(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle manual link rotation with comprehensive feedback"""
    try:
        base = text.split('/')[-1].lstrip('@')
        context.user_data['waiting_for_manual'] = False
        
        # Get registered channel or use current chat
        registered_channel = context.user_data.get('registered_channel')
        if not registered_channel:
            # Try to use current chat as channel
            chat_id = update.effective_chat.id
            registered_channel = f"chat_{chat_id}"
        
        # Show progress message
        progress_msg = await update.message.reply_text(
            f"🔄 در حال چرخش لینک کانال...\n"
            f"📡 کانال: {registered_channel}\n"
            f"🎯 نام جدید: @{base}\n"
            f"⏳ لطفاً صبر کنید..."
        )
        
        # Perform link rotation
        result = await change_public_link(registered_channel, base)
        
        if result["success"]:
            success_message = f"""✅ **چرخش لینک موفقیت‌آمیز!**

📡 **کانال:** {registered_channel}
🎯 **نام جدید:** @{result['new_username']}
🆔 **شناسه ردیابی:** {result['trace_id']}
✅ **تأیید شده:** بله
🔄 **تعداد تلاش:** {result['attempts']}

🔗 **لینک جدید:** https://t.me/{result['new_username']}"""
            
            await progress_msg.edit_text(success_message, reply_markup=main_menu())
        else:
            error_message = f"""❌ **چرخش لینک ناموفق!**

📡 **کانال:** {registered_channel}
🎯 **نام هدف:** @{base}
🆔 **شناسه ردیابی:** {result['trace_id']}
❌ **دلیل:** {result['reason']}
🔄 **تعداد تلاش:** {result['attempts']}

💡 **راهنمایی:** لطفاً مجوزهای ادمین را بررسی کنید."""
            
            await progress_msg.edit_text(error_message, reply_markup=main_menu())
            
    except Exception as e:
        logger.error("manual_link_rotation_failed", extra={
            "input": text,
            "error": str(e)
        })
        await update.message.reply_text(
            f'❌ خطا در چرخش لینک: {str(e)}', 
            reply_markup=main_menu()
        )

async def _handle_phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle phone number input"""
    phone = normalize_phone(text)
    if not phone:
        await update.message.reply_text('❌ شماره معتبر نیست. مثال: +989123456789')
        return
        
    context.user_data['waiting_for_phone'] = False
    await update.message.reply_text('📱 شماره ذخیره شد.', reply_markup=main_menu())

async def _get_health_matrix(channel_input: str) -> dict:
    """Get comprehensive health matrix for channel"""
    try:
        # Get telethon status
        telethon_status = get_status()
        
        if telethon_status != "ready":
            return {
                "telethon_status": telethon_status,
                "is_admin": "❌",
                "can_change_info": "❌",
                "can_view_participants": "❌",
                "status": "تنظیم‌نشده",
                "message": "⚠️ ابتدا Telethon را تنظیم کنید."
            }
        
        # Resolve channel and get permissions
        channel_info = await resolve_channel_from_input(channel_input)
        permissions = channel_info["permissions"]
        current_state = channel_info["current_state"]
        
        # Build health matrix
        is_admin = "✅" if permissions["is_admin"] else "❌"
        can_change_info = "✅" if permissions["can_change_info"] else "❌"
        can_view_participants = "✅" if permissions["can_view_participants"] else "❌"
        
        if permissions["is_admin"] and permissions["can_change_info"]:
            status = "آماده"
            message = "🎉 کانال آماده برای چرخش لینک است!"
        elif permissions["is_admin"]:
            status = "ناقص"
            message = "⚠️ ادمین هستید اما مجوز تغییر لینک ندارید."
        else:
            status = "نامناسب"
            message = "❌ ادمین کانال نیستید."
        
        return {
            "telethon_status": telethon_status,
            "is_admin": is_admin,
            "can_change_info": can_change_info,
            "can_view_participants": can_view_participants,
            "status": status,
            "message": message,
            "current_username": current_state.get("username"),
            "participants_count": current_state.get("participants_count", 0)
        }
        
    except Exception as e:
        logger.error("health_matrix_failed", extra={
            "channel_input": channel_input,
            "error": str(e)
        })
        return {
            "telethon_status": get_status(),
            "is_admin": "❓",
            "can_change_info": "❓",
            "can_view_participants": "❓",
            "status": "خطا",
            "message": f"❌ خطا در بررسی کانال: {str(e)}"
        }
