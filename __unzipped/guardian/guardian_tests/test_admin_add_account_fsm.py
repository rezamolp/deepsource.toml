
import pytest
from utils.validators import normalize_phone

@pytest.mark.parametrize("raw,expected", [
    ("+989123456789", "+989123456789"),
    ("09123456789", "+989123456789"),
    ("00989123456789", "+989123456789"),
    ("123", None),
])
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


import pytest

@pytest.mark.asyncio
async def test_invalid_number_handler(test_client, fsm_context):
    from handlers.admin_add_account import handle_phone_text
    class DummyMessage:
        text = "123"
        async def answer(self, msg): self.last_msg = msg
    msg = DummyMessage()
    state = fsm_context
    await handle_phone_text(msg, state)
    assert "شماره معتبر نیست" in msg.last_msg

@pytest.mark.asyncio
async def test_api_failure_logs(monkeypatch, caplog):
    from integrations.telegram_api import sign_in_safe
    class DummyClient:
        async def sign_in(self, *a, **kw): raise Exception("boom")
    client = DummyClient()
    result = await sign_in_safe(client, "+989123456789", "0000", trace_id="t1")
    assert "error" in result
    assert any("sign_in_failed" in r.message for r in caplog.records)
