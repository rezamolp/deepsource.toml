from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from telethon import TelegramClient
from telethon.errors import (PasswordHashInvalidError,
                             PhoneCodeExpiredError, PhoneCodeInvalidError,
                             SessionPasswordNeededError)

from .utils import mask


logger = logging.getLogger(__name__)


@dataclass
class TelethonLoginResult:
    ok: bool
    reason: str


class TelethonAccountManager:
    def __init__(self, api_id: int, api_hash: str, session_name: str = "sessions/guardian") -> None:
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self._client: Optional[TelegramClient] = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> TelegramClient:
        if self._client is None:
            self._client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self._client.connect()
        return self._client

    async def send_code(self, phone: str) -> TelethonLoginResult:
        async with self._lock:
            client = await self._get_client()
            try:
                await client.send_code_request(phone)
                return TelethonLoginResult(ok=True, reason="code_sent")
            except Exception as ex:
                logger.warning("telethon_send_code_failed", extra={"extra": {"phone": mask(phone), "error": str(ex)}})
                return TelethonLoginResult(ok=False, reason="send_code_failed")

    async def sign_in(self, phone: str, code: str, password: Optional[str] = None) -> TelethonLoginResult:
        async with self._lock:
            client = await self._get_client()
            try:
                await client.sign_in(phone=phone, code=code)
                return TelethonLoginResult(ok=True, reason="login_success")
            except SessionPasswordNeededError:
                if not password:
                    return TelethonLoginResult(ok=False, reason="2fa_needed")
                try:
                    await client.sign_in(phone=phone, password=password)
                    return TelethonLoginResult(ok=True, reason="login_success")
                except PasswordHashInvalidError:
                    return TelethonLoginResult(ok=False, reason="2fa_failed")
                except Exception:
                    return TelethonLoginResult(ok=False, reason="2fa_failed")
            except (PhoneCodeInvalidError, PhoneCodeExpiredError):
                return TelethonLoginResult(ok=False, reason="invalid_code")
            except Exception as ex:
                logger.warning("telethon_sign_in_failed", extra={"extra": {"phone": mask(phone), "error": str(ex)}})
                return TelethonLoginResult(ok=False, reason="login_failed")
