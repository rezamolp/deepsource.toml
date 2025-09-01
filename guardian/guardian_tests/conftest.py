import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

class DummyClient:
    def __init__(self):
        self.last_msg = None

    async def send_message(self, text):
        self.last_msg = text

@pytest.fixture
def test_client():
    """Fixture ساده برای شبیه‌سازی Bot Client در تست‌ها"""
    return DummyClient()

@pytest.fixture
def fsm_context():
    """Fixture ساختگی برای تست FSM"""
    class DummyFSM:
        def __init__(self):
            self.state = None
        async def set_state(self, state): self.state = state
        async def clear(self): self.state = None
    return DummyFSM()
