import logging
logger = logging.getLogger(__name__)

from typing import Optional, Dict
from config import API_ID, API_HASH

try:
    from telethon import TelegramClient
    from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneNumberInvalidError, FloodWaitError
except Exception:  # Telethon may not be available at build time
    TelegramClient = None  # type: ignore
    class SessionPasswordNeededError(Exception):
        pass
    class PhoneCodeInvalidError(Exception):
        pass
    class PhoneNumberInvalidError(Exception):
        pass
    class FloodWaitError(Exception):
        def __init__(self, seconds: int = 0): self.seconds = seconds

_client: Optional["TelegramClient"] = None
_phone_hash_by_phone: Dict[str, str] = {}
_phone_hash_by_trace: Dict[str, str] = {}

async def _get_client() -> Optional["TelegramClient"]:
    global _client
    if TelegramClient is None:
        logger.error("telethon_unavailable", extra={"event":"telethon_unavailable"})
        return None
    if _client is None:
        _client = TelegramClient("guardian", API_ID, API_HASH)
    if not await _client.connect():
        await _client.connect()
    return _client

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

# OTP / login flow using Telethon (falls back gracefully if not available)
async def send_code(phone: str, *, trace_id: str | None = None, user_id: str | None = None):
    client = await _get_client()
    if client is None:
        logger.error("send_code_failed", extra={"event":"send_code","phone":"***","trace_id":trace_id,"reason":"telethon_missing"})
        return {"error": "telethon_missing"}
    try:
        sent = await client.send_code_request(phone)
        # Telethon returns SentCode with phone_code_hash
        phone_code_hash = getattr(sent, 'phone_code_hash', None)
        if phone_code_hash:
            _phone_hash_by_phone[phone] = phone_code_hash
            if trace_id:
                _phone_hash_by_trace[trace_id] = phone_code_hash
        logger.info("send_code_ok", extra={"event":"send_code","trace_id":trace_id})
        return {"ok": True}
    except FloodWaitError as e:
        logger.error("send_code_flood", extra={"event":"send_code","trace_id":trace_id,"reason":"flood_wait","wait_seconds": getattr(e, 'seconds', 0)})
        return {"error": "flood_wait", "wait_seconds": getattr(e, 'seconds', 0)}
    except PhoneNumberInvalidError:
        logger.error("send_code_invalid_phone", extra={"event":"send_code","trace_id":trace_id,"reason":"phone_invalid"})
        return {"error": "phone_invalid"}
    except Exception as e:
        logger.error("send_code_error", extra={"event":"send_code","trace_id":trace_id,"reason":str(e)})
        return {"error": "unknown"}

async def confirm_code(phone: str, code: str, *, trace_id: str | None = None):
    client = await _get_client()
    if client is None:
        logger.error("confirm_code_failed", extra={"event":"confirm_code","trace_id":trace_id,"reason":"telethon_missing"})
        return {"error": "telethon_missing"}
    if not code or len(code) < 4:
        logger.error("confirm_code_failed", extra={"event":"confirm_code","trace_id":trace_id,"reason":"short_code"})
        return {"error": "invalid_code"}
    try:
        phone_code_hash = _phone_hash_by_trace.get(trace_id or "") or _phone_hash_by_phone.get(phone)
        # Telethon sign_in can work without explicit hash if last send_code_request used, but pass if we have
        if phone_code_hash:
            await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        else:
            await client.sign_in(phone=phone, code=code)
        logger.info("confirm_code_ok", extra={"event":"confirm_code","trace_id":trace_id})
        return {"ok": True}
    except SessionPasswordNeededError:
        logger.warning("confirm_code_2fa_needed", extra={"event":"confirm_code","trace_id":trace_id,"reason":"password_needed"})
        return {"error": "password_needed"}
    except PhoneCodeInvalidError:
        logger.error("confirm_code_invalid", extra={"event":"confirm_code","trace_id":trace_id,"reason":"code_invalid"})
        return {"error": "code_invalid"}
    except FloodWaitError as e:
        logger.error("confirm_code_flood", extra={"event":"confirm_code","trace_id":trace_id,"reason":"flood_wait","wait_seconds": getattr(e, 'seconds', 0)})
        return {"error": "flood_wait", "wait_seconds": getattr(e, 'seconds', 0)}
    except Exception as e:
        logger.error("confirm_code_error", extra={"event":"confirm_code","trace_id":trace_id,"reason":str(e)})
        return {"error": "unknown"}
