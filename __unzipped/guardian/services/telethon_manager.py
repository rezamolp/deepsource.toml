import logging
logger = logging.getLogger(__name__)

_client = None

def get_status() -> str:
    """وضعیت ساده telethon"""
    if _client:
        return "ready"
    return "not_configured"

# stub برای آینده
async def init_client():
    logger.info("telethon_init_called")
    return None

async def change_channel_link(channel_id: int, new_username: str):
    logger.info("change_channel_link_called", extra={"chat_id": channel_id, "new_username": new_username})
    return {"chat_id": channel_id, "new_username": new_username}

    class SessionPasswordNeededError(Exception):
        pass
