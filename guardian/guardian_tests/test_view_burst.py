
import time
from services.view_burst import ViewBurstDetector

def test_view_burst_triggers():
    vb = ViewBurstDetector(window_seconds=60, threshold=10)
    now = time.time()
    for i in range(10):
        assert not vb.add(1, now + i)
    # یازدهمی باید trigger کند
    assert vb.add(1, now + 11)


def test_view_burst_threshold_edges():
    vb = ViewBurstDetector(window_seconds=60, threshold=10)
    now = time.time()
    # 9 views نباید trigger کند
    for i in range(9):
        assert not vb.add(1, now + i)
    # دقیقا 10 باید trigger شود
    assert vb.add(1, now + 10)
