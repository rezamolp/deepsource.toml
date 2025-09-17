from __future__ import annotations

import os
from contextlib import contextmanager

import pytest

from guardian.config import load_settings


@contextmanager
def env_vars(**kwargs):
    old = {k: os.environ.get(k) for k in kwargs}
    try:
        for k, v in kwargs.items():
            os.environ[k] = str(v)
        yield
    finally:
        for k, v in old.items():
            if v is None and k in os.environ:
                del os.environ[k]
            elif v is not None:
                os.environ[k] = v


def test_load_settings_ok():
    with env_vars(
        BOT_TOKEN="x:1",
        ADMIN_ID="1",
        API_ID="123",
        API_HASH="abc",
        TARGET_CHAT_ID="-1001",
    ):
        s = load_settings()
        assert s.bot_token == "x:1"
        assert s.admin_id == 1
        assert s.api_id == 123
        assert s.api_hash == "abc"
        assert s.target_chat_id == -1001
