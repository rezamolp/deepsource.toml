
# Fallback exhaustion notification
async def notify_admin_on_fallback(admin_id: int, trace_id: str, bot):
    try:
        await bot.send_message(admin_id, f'⚠️ Guardian: همه تلاش‌های چرخش ناموفق بود. trace_id={trace_id}')
    except Exception as e:
        import logging; logging.error('failed_notify_admin', extra={'error': str(e)})

import asyncio, random
async def robust_notify_admin(admin_id: int, trace_id: str, bot, reason: str, retry_count: int = 3):
    last_err=None
    for _ in range(retry_count):
        try:
            await bot.send_message(admin_id, f'⚠️ Guardian: اعلان {reason} (trace_id={trace_id})')
            return True
        except Exception as e:
            last_err = e; await asyncio.sleep(1+random.random())
    import logging; logging.error('admin_notify_failed', extra={'error': str(last_err), 'trace_id': trace_id})
    return False
    try:
        await bot.send_message(admin_id, f'⚠️ Guardian: همه تلاش‌های چرخش ناموفق بود. trace_id={trace_id}')
    except Exception as e:
        import logging; logging.error('failed_notify_admin', extra={'error': str(e)})

    try:
        await bot.send_message(admin_id, f'⚠️ Guardian: همه تلاش‌های چرخش ناموفق بود. trace_id={trace_id}')
    except Exception as e:
        import logging; logging.error('failed_notify_admin', extra={'error': str(e)})

    try:
        text = f'⚠️ Guardian: همه تلاش‌های چرخش ({retry_count}) ناموفق بود. trace_id={trace_id}'
        await bot.send_message(admin_id, text)
    except Exception as e:
        import logging; logging.error('failed_notify_admin', extra={'error': str(e)})

    try:
        text = f'⚠️ Guardian: همه تلاش‌های چرخش ({retry_count}) ناموفق بود. trace_id={trace_id}'
        await bot.send_message(admin_id, text)
        # TODO: store retry_count in DB for forensic analysis
    except Exception as e:
        import logging; logging.error('failed_notify_admin', extra={'error': str(e)})

import asyncio, random
async def robust_notify_admin(admin_id: int, trace_id: str, bot, reason: str, retry_count: int = 3):
    last_err=None
    for attempt in range(retry_count):
        try:
            text = f'⚠️ Guardian: اعلان {reason} (trace_id={trace_id})'
            await bot.send_message(admin_id, text)
            return True
        except Exception as e:
            last_err = e
            await asyncio.sleep(1+random.random())
    import logging; logging.error('admin_notify_failed', extra={'error':str(last_err),'trace_id':trace_id})
    return False
