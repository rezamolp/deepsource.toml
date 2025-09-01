import pytest, time
from services.burst_detector import BurstDetector
from services.view_burst import ViewBurstDetector
from services.link_rotator import notify_admin_on_fallback

class DummyBot:
    def __init__(self): self.sent=[]
    async def send_message(self, chat_id, text): self.sent.append((chat_id,text))

def test_burst_prune():
    det = BurstDetector(window_seconds=1, threshold=2)
    det.add(time.time()-2)
    assert det.count()==0
    det.add(); det.add(); assert det.count()==2

def test_view_oscillation():
    det = ViewBurstDetector(window_seconds=60, threshold=10)
    assert not det.add(100)
    assert not det.add(-5)
    assert not det.add(10)

import asyncio
@pytest.mark.asyncio
async def test_notify_admin_on_fallback():
    bot=DummyBot()
    await notify_admin_on_fallback(123,'trace123',bot)
    assert bot.sent and 'trace123' in bot.sent[0][1]

import pytest, asyncio, time
from services.burst_detector import BurstDetector
from services.link_rotator import notify_admin_on_fallback
from integrations import telegram_api

def test_burst_prune_keeps_window():
    det = BurstDetector(window_seconds=1, threshold=2)
    det.add(time.time()-2)
    assert det.count()==0
    det.add(); det.add(); assert det.count()>=2

@pytest.mark.asyncio
async def test_rotation_fallback_notify():
    class DummyBot:
        def __init__(self): self.sent=[]
        async def send_message(self, cid, txt): self.sent.append((cid,txt))
    bot=DummyBot()
    await notify_admin_on_fallback(123,'traceXYZ',bot)
    assert bot.sent and 'traceXYZ' in bot.sent[0][1]

def test_2fa_logging_and_mask():
    telegram_api.log_2fa_required(42)
    telegram_api.log_2fa_failed(42)
    assert telegram_api.mask_password('secret')=='****'

import pytest, asyncio, time
from services.burst_detector import BurstDetector
from services.link_rotator import notify_admin_on_fallback
from integrations import telegram_api

def test_burst_prune_removes_old():
    det = BurstDetector(window_seconds=1, threshold=2)
    det.add(time.time()-2)
    assert det.count()==0
    det.add(); det.add(); assert det.count()>=2

@pytest.mark.asyncio
async def test_rotation_notify_admin():
    class DummyBot:
        def __init__(self): self.sent=[]
        async def send_message(self,cid,txt): self.sent.append((cid,txt))
    bot=DummyBot()
    await notify_admin_on_fallback(123,'traceZ',bot,5)
    assert bot.sent and 'traceZ' in bot.sent[0][1]

def test_2fa_logging_and_mask():
    telegram_api.log_2fa_required(42,'tid')
    telegram_api.log_2fa_failed(42,'tid')
    assert telegram_api.mask_secret('secret')=='****'

import pytest, asyncio, time
from services.burst_detector import BurstDetector
from services.link_rotator import notify_admin_on_fallback
from integrations import telegram_api

def test_burst_prune_window():
    det = BurstDetector(window_seconds=1, threshold=2)
    det.add(time.time()-2)
    assert det.count()==0
    det.add(); det.add(); assert det.count()>=2

@pytest.mark.asyncio
async def test_rotation_exhaustion_notify():
    class DummyBot:
        def __init__(self): self.sent=[]
        async def send_message(self,cid,txt): self.sent.append((cid,txt))
    bot=DummyBot()
    await notify_admin_on_fallback(123,'traceY',bot,100)
    assert bot.sent and 'traceY' in bot.sent[0][1]

def test_2fa_fail_logging():
    telegram_api.log_2fa_required(42,'tid')
    telegram_api.log_2fa_failed(42,'tid')
    assert telegram_api.mask_secret('mypassword')=='****'

from services import antispam_lock
def test_double_trigger_guard():
    key=('chat1','join')
    assert antispam_lock.acquire(1,'join')
    assert not antispam_lock.acquire(1,'join')
    time.sleep(2)
    assert antispam_lock.acquire(1,'join')

import pytest, asyncio
@pytest.mark.asyncio
async def test_admin_notify_failure(monkeypatch):
    class DummyBot:
        async def send_message(self, cid, txt):
            raise Exception('dm blocked')
    bot=DummyBot()
    from services.link_rotator import robust_notify_admin
    ok = await robust_notify_admin(123,'traceX',bot,'fallback_exhausted',retry_count=2)
    assert not ok
