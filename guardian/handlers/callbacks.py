from telegram import Update
from telegram.ext import ContextTypes
from utils.data import load_data, save_data
from services.telethon_manager import get_status
from services.channel import get_rotation_status, get_rotation_statistics
from handlers.commands import main_menu
import logging

logger = logging.getLogger(__name__)

antispam_enabled = True

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()

    if query.data == "status":
        await _handle_status_request(update, context)
    elif query.data == "set_channel":
        context.user_data["waiting_for_channel"] = True
        await query.edit_message_text(
            "📡 نام کاربری کانال (@name یا t.me/...) را بفرست.\n\n"
            "💡 مثال:\n"
            "• @mychannel\n"
            "• https://t.me/mychannel\n"
            "• mychannel", 
            reply_markup=main_menu()
        )
    elif query.data == "manual_link":
        context.user_data["waiting_for_manual"] = True
        await query.edit_message_text(
            "🎯 نام کاربری جهت چرخش لینک را بفرست.\n\n"
            "💡 مثال:\n"
            "• guardian\n"
            "• mybot\n"
            "• channel", 
            reply_markup=main_menu()
        )
    elif query.data == "add_account":
        context.user_data["waiting_for_phone"] = True
        await query.edit_message_text(
            "📱 شمارهٔ تلفن را بفرست (مثال: +98912...)\n\n"
            "⚠️ این شماره باید در کانال ادمین باشد.", 
            reply_markup=main_menu()
        )
    elif query.data == "rotation_stats":
        await _handle_rotation_stats(update, context)
    elif query.data == "health_check":
        await _handle_health_check(update, context)
    else:
        await query.edit_message_text("دستور ناشناخته.", reply_markup=main_menu())

async def _handle_status_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle status request with comprehensive information"""
    query = update.callback_query
    
    try:
        # Get basic status
        telethon_status = get_status()
        telethon_status_text = "✅ آماده" if telethon_status == "ready" else "❌ تنظیم‌نشده"
        
        # Get rotation statistics
        stats = get_rotation_statistics()
        
        # Get registered channel info if available
        registered_channel = context.user_data.get('registered_channel')
        channel_status = "❌ تنظیم‌نشده"
        channel_health = ""
        
        if registered_channel:
            try:
                rotation_status = await get_rotation_status(registered_channel)
                if "channel_info" in rotation_status:
                    channel_info = rotation_status["channel_info"]
                    if "error" not in channel_info:
                        current_state = channel_info["current_state"]
                        permissions = channel_info["permissions"]
                        
                        channel_status = f"✅ @{registered_channel}"
                        channel_health = f"""
📊 **وضعیت کانال:**
👑 **ادمین:** {'✅' if permissions['is_admin'] else '❌'}
🔧 **مجوز تغییر:** {'✅' if permissions['can_change_info'] else '❌'}
👥 **نام فعلی:** @{current_state.get('username', 'بدون نام')}
👥 **اعضا:** {current_state.get('participants_count', 0)} نفر"""
                    else:
                        channel_status = f"❌ خطا: {channel_info['error']}"
            except Exception as e:
                channel_status = f"❌ خطا: {str(e)}"
        
        # Build comprehensive status message
        status_message = f"""📊 **وضعیت سیستم Guardian**

🤖 **ضداسپم:** {'✅ فعال' if antispam_enabled else '❌ غیرفعال'}
📡 **Telethon:** {telethon_status_text}
📺 **کانال:** {channel_status}

📈 **آمار چرخش:**
✅ **موفق:** {stats['success_count']} بار
❌ **ناموفق:** {stats['fail_count']} بار
🔄 **آخرین پسوند:** {stats['last_suffix']}

{channel_health}

💡 **راهنمایی:** برای شروع، ابتدا کانال را تنظیم کنید."""

        await query.edit_message_text(status_message, reply_markup=main_menu())
        
    except Exception as e:
        logger.error("status_request_failed", extra={"error": str(e)})
        await query.edit_message_text(
            f"❌ خطا در دریافت وضعیت: {str(e)}", 
            reply_markup=main_menu()
        )

async def _handle_rotation_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle detailed rotation statistics request"""
    query = update.callback_query
    
    try:
        stats = get_rotation_statistics()
        
        # Calculate success rate
        total_attempts = stats['success_count'] + stats['fail_count']
        success_rate = (stats['success_count'] / total_attempts * 100) if total_attempts > 0 else 0
        
        # Format last rotation time
        last_time = "هرگز" if not stats['last_rotation_time'] else "اخیراً"
        
        stats_message = f"""📊 **آمار تفصیلی چرخش لینک**

✅ **موفقیت‌ها:** {stats['success_count']} بار
❌ **شکست‌ها:** {stats['fail_count']} بار
📈 **نرخ موفقیت:** {success_rate:.1f}%
🔄 **آخرین پسوند:** {stats['last_suffix']}
⏰ **آخرین چرخش:** {last_time}

📋 **تجزیه و تحلیل:**
{'🎉 عملکرد عالی!' if success_rate >= 80 else '⚠️ نیاز به بهبود' if success_rate >= 50 else '❌ مشکل جدی'}

💡 **پیشنهادات:**
• بررسی مجوزهای ادمین
• اطمینان از آزاد بودن نام‌های کاربری
• بررسی وضعیت اتصال Telethon"""

        await query.edit_message_text(stats_message, reply_markup=main_menu())
        
    except Exception as e:
        logger.error("rotation_stats_failed", extra={"error": str(e)})
        await query.edit_message_text(
            f"❌ خطا در دریافت آمار: {str(e)}", 
            reply_markup=main_menu()
        )

async def _handle_health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle comprehensive health check"""
    query = update.callback_query
    
    try:
        # Get telethon status
        telethon_status = get_status()
        
        # Get registered channel health
        registered_channel = context.user_data.get('registered_channel')
        
        if not registered_channel:
            health_message = f"""🔍 **بررسی سلامت سیستم**

📡 **Telethon:** {'✅ آماده' if telethon_status == 'ready' else '❌ تنظیم‌نشده'}
📺 **کانال:** ❌ تنظیم‌نشده

⚠️ **اقدامات لازم:**
1. تنظیم Telethon
2. ثبت کانال هدف

💡 برای شروع، دکمه «تنظیم کانال» را بزنید."""
        else:
            try:
                from services.channel import resolve_channel_from_input
                channel_info = await resolve_channel_from_input(registered_channel)
                permissions = channel_info["permissions"]
                current_state = channel_info["current_state"]
                
                # Build health status
                health_score = 0
                issues = []
                
                if telethon_status == "ready":
                    health_score += 25
                else:
                    issues.append("Telethon تنظیم نشده")
                
                if permissions["is_admin"]:
                    health_score += 25
                else:
                    issues.append("ادمین کانال نیستید")
                
                if permissions["can_change_info"]:
                    health_score += 25
                else:
                    issues.append("مجوز تغییر لینک ندارید")
                
                if current_state.get("username"):
                    health_score += 25
                else:
                    issues.append("کانال نام کاربری ندارد")
                
                # Determine overall health
                if health_score == 100:
                    health_status = "🟢 عالی"
                    status_emoji = "🎉"
                elif health_score >= 75:
                    health_status = "🟡 خوب"
                    status_emoji = "✅"
                elif health_score >= 50:
                    health_status = "🟠 متوسط"
                    status_emoji = "⚠️"
                else:
                    health_status = "🔴 ضعیف"
                    status_emoji = "❌"
                
                health_message = f"""🔍 **بررسی سلامت سیستم**

📊 **امتیاز کلی:** {health_score}/100 {health_status}

📡 **Telethon:** {'✅ آماده' if telethon_status == 'ready' else '❌ تنظیم‌نشده'}
📺 **کانال:** @{registered_channel}
👑 **ادمین:** {'✅' if permissions['is_admin'] else '❌'}
🔧 **مجوز تغییر:** {'✅' if permissions['can_change_info'] else '❌'}
👥 **نام فعلی:** @{current_state.get('username', 'بدون نام')}

{status_emoji} **وضعیت:** {health_status}

{'✅ سیستم آماده برای چرخش لینک!' if health_score == 100 else f'⚠️ مشکلات موجود:\n' + '\n'.join(f'• {issue}' for issue in issues)}"""

            except Exception as e:
                health_message = f"""🔍 **بررسی سلامت سیستم**

❌ **خطا در بررسی کانال:** {str(e)}

📡 **Telethon:** {'✅ آماده' if telethon_status == 'ready' else '❌ تنظیم‌نشده'}
📺 **کانال:** @{registered_channel}

💡 لطفاً کانال را مجدداً تنظیم کنید."""

        await query.edit_message_text(health_message, reply_markup=main_menu())
        
    except Exception as e:
        logger.error("health_check_failed", extra={"error": str(e)})
        await query.edit_message_text(
            f"❌ خطا در بررسی سلامت: {str(e)}", 
            reply_markup=main_menu()
        )
