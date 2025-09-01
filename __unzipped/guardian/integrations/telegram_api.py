import logging
import asyncio
from telethon.errors import SessionPasswordNeededError


class TelegramAPI:
    def __init__(self, bot, repo):
        self.bot = bot
        self.repo = repo
        self.logger = logging.getLogger(__name__)

    async def create_chat_invite_link(self, chat_id, expire_date=None):
        try:
            return await self.bot.create_chat_invite_link(chat_id, expire_date=expire_date)
        except Exception as e:
            self.logger.error("invite_link_error", extra={"error": str(e)})
            return None

    async def revoke_invite_link(self, chat_id, invite_link):
        try:
            return await self.bot.revoke_chat_invite_link(chat_id, invite_link)
        except Exception as e:
            self.logger.error("revoke_link_error", extra={"error": str(e)})
            return None

    async def try_set_username(self, chat_id, username):
        try:
            return await self.bot.set_chat_username(chat_id, username)
        except Exception:
            return False


logger = logging.getLogger(__name__)

async def sign_in(client, phone: str, code: str, password: str | None = None):
    try:
        return await client.sign_in(phone=phone, code=code)
    except SessionPasswordNeededError:
        if not password:
            raise
        return await client.sign_in(password=password)


async def sign_in_safe(client, phone: str, code: str, password: str | None = None, trace_id: str | None = None):
    try:
        return await client.sign_in(phone=phone, code=code)
    except SessionPasswordNeededError:
        if not password:
            logger.error("password_required", extra={"trace_id": trace_id or "unknown", "phone": phone})
            return {"error": "رمز عبور نیاز است."}
        return await client.sign_in(password=password)
    except Exception as e:
        logger.error("sign_in_failed", extra={"trace_id": trace_id or "unknown", "phone": phone, "error": str(e)})
        return {"error": "ورود ناموفق بود، لطفاً دوباره تلاش کنید."}


async def login_with_2fa(client, phone, code_callback, password_callback):
    try:
        await client.start(phone=phone, code_callback=code_callback)
    except SessionPasswordNeededError:
        for _ in range(3):
            try:
                pw = await password_callback()
                await client.sign_in(password=pw)
                return True
            except Exception:
                await asyncio.sleep(2)
        raise


def mask_secret(_: str) -> str:
    return "****"

def log_2fa_required(user_id, trace_id=None):
    logging.warning("2fa_required", extra={"user_id": user_id, "trace_id": trace_id})

def log_2fa_failed(user_id, trace_id=None):
    logging.error("2fa_failed", extra={"user_id": user_id, "trace_id": trace_id})
