
import time
import pytest
from services.burst_detector import BurstDetector

def test_burst_eviction_and_count(monkeypatch):
    bd = BurstDetector(window_seconds=1)
    now = time.time()
    bd.add(now - 2)
    bd.add(now)
    assert bd.count_recent() == 1
    bd.add(now + 0.5)
    assert bd.count_recent() == 2
