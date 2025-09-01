import asyncio, random, logging
from utils.data import load_data, save_data
from services.antispam_lock import acquire as acquire_lock
from services.telethon_manager import get_status as telethon_status
from services.channel import change_public_link

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

async def rotate_username(context, chat_id: int, base_username: str, trace_id: str | None = None):
    """Try rotating public username base→base1..base100, then fallback to invite.
    Updates telemetry counters on success/failure.
    """
    logger = logging.getLogger(__name__)
    if not acquire_lock(chat_id, 'rotation'):
        logger.info('rotation_skipped_locked', extra={'event':'rotation','chat_id':chat_id})
        return {'error':'locked'}
    data = load_data() or {}
    try:
        new_link = await change_public_link(chat_id, base_username, context=context)
        # success: may be username or invite link string
        data['link_changes_success'] = int(data.get('link_changes_success', 0)) + 1
        data['last_rotation_link'] = new_link
        import time
        data['last_rotation_at'] = int(time.time())
        save_data(data)
        logger.info('rotation_ok', extra={'event':'rotation_ok','chat_id':chat_id,'new_link':'***','trace_id':trace_id})
        return {'ok': True, 'link': new_link}
    except Exception as e:
        data['link_changes_fail'] = int(data.get('link_changes_fail', 0)) + 1
        save_data(data)
        logger.error('rotation_fail', extra={'event':'rotation_fail','chat_id':chat_id,'reason':str(e),'trace_id':trace_id})
        return {'error': str(e)}
