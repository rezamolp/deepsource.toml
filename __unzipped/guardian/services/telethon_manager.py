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

# OTP / login flow stubs
async def send_code(phone: str, *, trace_id: str | None = None):
    logger.info("send_code_called", extra={"event":"send_code","phone": phone, "trace_id": trace_id})
    return {"ok": True}

async def confirm_code(phone: str, code: str, *, trace_id: str | None = None):
    if not code or len(code) < 4:
        logger.error("confirm_code_failed", extra={"event":"confirm_code","phone": phone, "trace_id": trace_id, "reason": "short_code"})
        return {"error": "invalid_code"}
    logger.info("confirm_code_ok", extra={"event":"confirm_code","phone": phone, "trace_id": trace_id})
    return {"ok": True}
