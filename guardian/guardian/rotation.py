from __future__ import annotations

import asyncio
import logging
from typing import Optional

from telethon import TelegramClient
from telethon.errors import UsernameOccupiedError
from telethon.tl.functions.channels import UpdateUsernameRequest
from telethon.tl.functions.messages import ExportChatInviteRequest

from .utils import generate_trace_id


class LinkRotationManager:
    def __init__(self, api_id: int, api_hash: str, session_name: str = "sessions/guardian") -> None:
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self._client: Optional[TelegramClient] = None
        self._lock = asyncio.Lock()

    async def _ensure_client(self) -> TelegramClient:
        if self._client is None:
            self._client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self._client.connect()
        return self._client

    async def rotate(self, chat_id: int, base: str, max_suffix: int) -> tuple[str, str]:
        """Try to set public username base or suffixed; otherwise fallback to invite link.

        Returns (new_link, reason) where reason is 'username' or 'invite'.
        """
        async with self._lock:
            client = await self._ensure_client()
            entity = await client.get_input_entity(chat_id)
            # Try base first then 1..max_suffix
            for suffix in [None] + list(range(1, max_suffix + 1)):
                try_username = base if suffix is None else f"{base}{suffix}"
                try:
                    await client(UpdateUsernameRequest(channel=entity, username=try_username))
                    return f"https://t.me/{try_username}", "username"
                except UsernameOccupiedError:
                    continue
                except Exception:
                    # Ignore and try next
                    continue

            # Fallback: remove username and create private invite link
            try:
                await client(UpdateUsernameRequest(channel=entity, username=""))
            except Exception:
                pass
            invite = await client(ExportChatInviteRequest(peer=entity))
            return invite.link, "invite"
