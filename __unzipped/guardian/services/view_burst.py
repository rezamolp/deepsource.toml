import time
from collections import deque

class ViewBurstDetector:
    def __init__(self, window_seconds=60, threshold=50):
        self.window_seconds = window_seconds
        self.threshold = threshold
        self.events = deque()
        self.total = 0
        self._last_views = None
    def _prune(self, now: float):
        while self.events and (now - self.events[0][0]) > self.window_seconds:
            _, v = self.events.popleft()
            self.total -= v

    def add(self, views:int, ts:float|None=None):
        ts = ts or time.time()
        # baseline/delta auto-detect for first sample:
        # - If first value is small (<= threshold), treat as delta (accumulate)
        # - If it's large, treat as absolute baseline (no trigger)
        if self._last_views is None:
            if views <= self.threshold:
                self.events.append((ts, views))
                self.total += views
                self._last_views = views
                self._prune(ts)
                return self.total >= self.threshold
            else:
                self._last_views = views
                self._prune(ts)
                return False

        if views <= 0:
            self._prune(ts)
            return False
        # compute positive delta relative to last sample
        delta = max(0, views - self._last_views)
        self._last_views = views
        if delta == 0:
            self._prune(ts)
            return self.total >= self.threshold
        # append then prune window consistently using delta
        self.events.append((ts, delta))
        self.total += delta
        self._prune(ts)
        # inclusive threshold: trigger when total >= threshold
        return self.total >= self.threshold
