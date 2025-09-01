import asyncio, random, logging

async def robust_notify_admin(admin_id: int, trace_id: str, bot, reason: str, retry_count: int = 3):
    last_err = None
    for _ in range(retry_count):
        try:
            await bot.send_message(admin_id, f'⚠️ Guardian: اعلان {reason} (trace_id={trace_id})')
            return True
        except Exception as e:
            last_err = e
            await asyncio.sleep(1 + random.random())
    logging.error('admin_notify_failed', extra={'error': str(last_err), 'trace_id': trace_id})
    return False

async def notify_admin_on_fallback(admin_id: int, trace_id: str, bot):
    try:
        await bot.send_message(admin_id, f'⚠️ Guardian: همه تلاش‌های چرخش ناموفق بود. trace_id={trace_id}')
        return True
    except Exception as e:
        logging.error('failed_notify_admin', extra={'error': str(e), 'trace_id': trace_id})
        return False
