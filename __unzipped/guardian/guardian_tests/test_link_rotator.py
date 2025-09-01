# Telethon dependency removed for testing

import pytest
import asyncio
from services import channel

@pytest.mark.asyncio
async def test_link_rotation_success(monkeypatch):
    async def fake_change(cid, uname): return {"ok": True}
    monkeypatch.setattr("services.telethon_manager.change_channel_link", fake_change)
    new_uname = await channel.change_public_link(123, "testchan")
    assert new_uname.startswith("testchan")
