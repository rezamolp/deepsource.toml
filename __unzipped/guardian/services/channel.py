import logging
from services import telethon_manager
from telegram.error import BadRequest
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)
_last_suffix = 0

async def change_public_link(channel_id: int, base_username: str, *, context: ContextTypes.DEFAULT_TYPE | None = None):
    global _last_suffix
    for i in range(_last_suffix+1,101):
        new_username = f"{base_username}{i}"
        try:
            await telethon_manager.change_channel_link(channel_id,new_username)
            _last_suffix = i
            logger.info('link_rotation_success', extra={'chat_id':channel_id,'new_username':new_username})
            return new_username
        except Exception as e:
            logger.warning('link_rotation_attempt_failed', extra={'chat_id': channel_id, 'new_username': new_username, 'error': str(e)})
            continue
    _last_suffix=0
    # Fallback: create invite link if available via context.bot
    if context is not None:
        try:
            invite = await context.bot.create_chat_invite_link(chat_id=channel_id)
            logger.info('fallback_invite_created', extra={'chat_id': channel_id})
            return invite.invite_link if hasattr(invite, 'invite_link') else str(invite)
        except Exception as e:
            logger.error('fallback_invite_failed', extra={'chat_id': channel_id, 'error': str(e)})
    raise RuntimeError('link rotation failed after 100 attempts and fallback')
