import time
from collections import deque

class BurstDetector:
    def __init__(self, window_seconds:int, threshold:int = 10):
        if window_seconds < 1 or threshold < 1:
            raise ValueError("window_seconds and threshold must be >= 1")
        self.window_seconds = window_seconds
        self.threshold = threshold
        self.events = deque()

    def prune(self, now=None):
        if now is None:
            now = time.time()
        while self.events and self.events[0] < now - self.window_seconds:
            self.events.popleft()

    def add(self, ts=None):
        if ts is None:
            ts = time.time()
        self.prune(ts)
        self.events.append(ts)

    def count_recent(self, now=None):
        self.prune(now or time.time())
        return len(self.events)

    def is_burst(self, now=None):
        return self.count_recent(now or time.time()) >= self.threshold

    def count(self):
        return self.count_recent()
