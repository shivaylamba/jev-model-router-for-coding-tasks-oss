"""A fake clock and sleep for driving asyncio code in tests without real time."""

import asyncio


async def settle(rounds=50):
    """Let ready tasks run until the event loop is idle (no real time passes)."""
    for _ in range(rounds):
        await asyncio.sleep(0)


class FakeTime:
    """`clock()` returns `now`; `sleep(d)` completes once `advance` moves `now` to its deadline."""

    def __init__(self, start=0.0):
        self.now = start
        self.sleep_calls = []
        self._sleepers = []

    def clock(self):
        return self.now

    async def sleep(self, delay):
        self.sleep_calls.append(delay)
        if delay <= 0:
            await asyncio.sleep(0)
            return
        entry = (self.now + delay, asyncio.get_running_loop().create_future())
        self._sleepers.append(entry)
        try:
            await entry[1]
        finally:
            if entry in self._sleepers:
                self._sleepers.remove(entry)

    async def advance(self, seconds):
        """Move the clock forward, wake every sleeper that is due, and let tasks run."""
        self.now += seconds
        for _ in range(20):
            for entry in [entry for entry in self._sleepers if entry[0] <= self.now]:
                self._sleepers.remove(entry)
                if not entry[1].done():
                    entry[1].set_result(None)
            await settle()
            if not any(entry[0] <= self.now for entry in self._sleepers):
                return
