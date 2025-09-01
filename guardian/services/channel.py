import logging
from services import telethon_manager

logger = logging.getLogger(__name__)
_last_suffix = 0

async def change_public_link(channel_id: int, base_username: str):
    global _last_suffix
    for i in range(_last_suffix+1,101):
        new_username = f"{base_username}{i}"
        try:
            await telethon_manager.change_channel_link(channel_id,new_username)
            _last_suffix = i
            logger.info('link_rotation_success', extra={'chat_id':channel_id,'new_username':new_username})
            return new_username
        except Exception as e:
            logger.warning('link_rotation_attempt_failed',extra={'chat_id':channel_id,'new_username':new_username,'error':str(e)})
            continue
    _last_suffix=0
    raise RuntimeError('link rotation failed after 100 attempts')
