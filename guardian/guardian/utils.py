from __future__ import annotations

import asyncio
import logging
import secrets
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Optional, Tuple


class ConcurrencyGuard:
    """A lightweight per-(chat_id, kind) async lock with a small TTL window.

    Prevents duplicate rotations when join and view bursts are detected together.
    """

    def __init__(self) -> None:
        self._locks: Dict[Tuple[int, str], asyncio.Lock] = {}

    @asynccontextmanager
    async def acquire(self, chat_id: int, kind: str) -> AsyncIterator[bool]:
        key = (chat_id, kind)
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        acquired = await lock.acquire()
        try:
            yield acquired
        finally:
            try:
                lock.release()
            except RuntimeError:
                pass


def generate_trace_id() -> str:
    return secrets.token_hex(6)


def mask(value: Optional[str]) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 4) + value[-2:]
