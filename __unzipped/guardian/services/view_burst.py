import time
from collections import deque

class ViewBurstDetector:
    def __init__(self, window_seconds=60, threshold=50):
        self.window_seconds = window_seconds
        self.threshold = threshold
        self.events = deque()
        self.total = 0
    def add(self, views:int, ts:float|None=None):
        ts = ts or time.time()
        self.events.append((ts,views))
        if views <= 0 or views >= self.threshold:
            return False
        self.total += views
        while self.events and ts - self.events[0][0] > self.window_seconds:
            _,v=self.events.popleft(); self.total-=v
        return self.total>self.threshold
