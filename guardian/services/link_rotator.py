import asyncio
import random
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

async def notify_admin_on_fallback(admin_id: int, trace_id: str, bot, reason: str = "fallback_exhausted"):
    """
    Notify admin when all rotation attempts fail
    """
    try:
        message = f"""⚠️ **هشدار Guardian**

🔄 **موضوع:** چرخش لینک ناموفق
🆔 **شناسه ردیابی:** {trace_id}
❌ **دلیل:** {reason}

💡 **اقدامات پیشنهادی:**
• بررسی مجوزهای ادمین
• اطمینان از آزاد بودن نام‌های کاربری
• بررسی وضعیت اتصال Telethon"""
        
        await bot.send_message(admin_id, message)
        logger.info("admin_notified_fallback", extra={
            "admin_id": admin_id,
            "trace_id": trace_id,
            "reason": reason
        })
        return True
        
    except Exception as e:
        logger.error("admin_notification_failed", extra={
            "admin_id": admin_id,
            "trace_id": trace_id,
            "error": str(e)
        })
        return False

async def robust_notify_admin(admin_id: int, trace_id: str, bot, reason: str, retry_count: int = 3):
    """
    Robust admin notification with retry mechanism
    """
    last_err = None
    
    for attempt in range(retry_count):
        try:
            message = f"""📢 **اعلان Guardian**

🔄 **موضوع:** {reason}
🆔 **شناسه ردیابی:** {trace_id}
📊 **تلاش:** {attempt + 1}/{retry_count}"""
            
            await bot.send_message(admin_id, message)
            
            logger.info("admin_notification_success", extra={
                "admin_id": admin_id,
                "trace_id": trace_id,
                "reason": reason,
                "attempt": attempt + 1
            })
            return True
            
        except Exception as e:
            last_err = e
            logger.warning("admin_notification_attempt_failed", extra={
                "admin_id": admin_id,
                "trace_id": trace_id,
                "reason": reason,
                "attempt": attempt + 1,
                "error": str(e)
            })
            
            # Wait before retry with exponential backoff
            if attempt < retry_count - 1:
                wait_time = 1 + random.random() + (attempt * 0.5)
                await asyncio.sleep(wait_time)
    
    # All attempts failed
    logger.error("admin_notification_all_attempts_failed", extra={
        "admin_id": admin_id,
        "trace_id": trace_id,
        "reason": reason,
        "retry_count": retry_count,
        "last_error": str(last_err)
    })
    return False

async def notify_rotation_success(admin_id: int, trace_id: str, bot, channel_info: Dict[str, Any]):
    """
    Notify admin of successful rotation
    """
    try:
        message = f"""✅ **چرخش لینک موفقیت‌آمیز!**

📡 **کانال:** {channel_info.get('channel_id', 'نامشخص')}
🎯 **نام جدید:** @{channel_info.get('new_username', 'نامشخص')}
🆔 **شناسه ردیابی:** {trace_id}
✅ **تأیید شده:** بله
🔄 **تعداد تلاش:** {channel_info.get('attempts', 0)}

🔗 **لینک جدید:** https://t.me/{channel_info.get('new_username', '')}

🎉 **عملیات با موفقیت انجام شد!**"""
        
        await bot.send_message(admin_id, message)
        logger.info("rotation_success_notified", extra={
            "admin_id": admin_id,
            "trace_id": trace_id,
            "channel_info": channel_info
        })
        return True
        
    except Exception as e:
        logger.error("rotation_success_notification_failed", extra={
            "admin_id": admin_id,
            "trace_id": trace_id,
            "error": str(e)
        })
        return False

async def notify_rotation_failure(admin_id: int, trace_id: str, bot, channel_info: Dict[str, Any], reason: str):
    """
    Notify admin of rotation failure
    """
    try:
        message = f"""❌ **چرخش لینک ناموفق!**

📡 **کانال:** {channel_info.get('channel_id', 'نامشخص')}
🎯 **نام هدف:** {channel_info.get('target_username', 'نامشخص')}
🆔 **شناسه ردیابی:** {trace_id}
❌ **دلیل:** {reason}
🔄 **تعداد تلاش:** {channel_info.get('attempts', 0)}

💡 **راهنمایی:**
• بررسی مجوزهای ادمین
• اطمینان از آزاد بودن نام‌های کاربری
• بررسی وضعیت اتصال Telethon

🔍 برای اطلاعات بیشتر، دکمه «بررسی سلامت» را بزنید."""
        
        await bot.send_message(admin_id, message)
        logger.info("rotation_failure_notified", extra={
            "admin_id": admin_id,
            "trace_id": trace_id,
            "channel_info": channel_info,
            "reason": reason
        })
        return True
        
    except Exception as e:
        logger.error("rotation_failure_notification_failed", extra={
            "admin_id": admin_id,
            "trace_id": trace_id,
            "error": str(e)
        })
        return False

async def notify_permission_error(admin_id: int, trace_id: str, bot, channel_id: int, permissions: Dict[str, Any]):
    """
    Notify admin of permission issues
    """
    try:
        message = f"""⛔ **خطای مجوز!**

📡 **کانال:** {channel_id}
🆔 **شناسه ردیابی:** {trace_id}

📊 **وضعیت مجوزها:**
👑 **ادمین:** {'✅' if permissions.get('is_admin') else '❌'}
🔧 **مجوز تغییر:** {'✅' if permissions.get('can_change_info') else '❌'}
👥 **مجوز مشاهده:** {'✅' if permissions.get('can_view_participants') else '❌'}

❌ **دلیل:** {permissions.get('reason', 'نامشخص')}

💡 **راهنمایی:**
• اطمینان از ادمین بودن در کانال
• بررسی مجوز «تغییر اطلاعات»
• درخواست مجوز از مالک کانال"""
        
        await bot.send_message(admin_id, message)
        logger.info("permission_error_notified", extra={
            "admin_id": admin_id,
            "trace_id": trace_id,
            "channel_id": channel_id,
            "permissions": permissions
        })
        return True
        
    except Exception as e:
        logger.error("permission_error_notification_failed", extra={
            "admin_id": admin_id,
            "trace_id": trace_id,
            "error": str(e)
        })
        return False

async def notify_telethon_status(admin_id: int, bot, status: str, details: str = ""):
    """
    Notify admin of Telethon status changes
    """
    try:
        if status == "ready":
            message = f"""✅ **Telethon آماده!**

📡 **وضعیت:** اتصال برقرار
🔗 **جزئیات:** {details}

🎉 سیستم آماده برای چرخش لینک است!"""
        else:
            message = f"""❌ **مشکل Telethon!**

📡 **وضعیت:** {status}
🔗 **جزئیات:** {details}

⚠️ لطفاً Telethon را مجدداً تنظیم کنید."""
        
        await bot.send_message(admin_id, message)
        logger.info("telethon_status_notified", extra={
            "admin_id": admin_id,
            "status": status,
            "details": details
        })
        return True
        
    except Exception as e:
        logger.error("telethon_status_notification_failed", extra={
            "admin_id": admin_id,
            "error": str(e)
        })
        return False
