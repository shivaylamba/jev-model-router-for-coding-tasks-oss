"""Clocks. Times are float seconds."""

import time


class SystemClock:
    def now(self):
        return time.time()


class ManualClock:
    """A clock that only moves when told to."""

    def __init__(self, start=0.0):
        self._now = float(start)

    def now(self):
        return self._now

    def advance(self, seconds):
        self._now += seconds
