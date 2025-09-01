import time
from collections import deque

class ViewBurstDetector:
    def __init__(self, window_seconds=60, threshold=50):
        self.window_seconds = window_seconds
        self.threshold = threshold
        self.events = deque()
        self.total = 0
    def _prune(self, now: float):
        while self.events and (now - self.events[0][0]) > self.window_seconds:
            _, v = self.events.popleft()
            self.total -= v

    def add(self, views:int, ts:float|None=None):
        ts = ts or time.time()
        if views <= 0:
            self._prune(ts)
            return False
        # append then prune window consistently
        self.events.append((ts, views))
        self.total += views
        self._prune(ts)
        # inclusive threshold: trigger when total >= threshold
        return self.total >= self.threshold
