"""Asyncio rate limiter: per-key token buckets plus a global concurrency cap.

See SPEC.md for the full behaviour.
"""

import asyncio
import itertools
from collections import deque
from contextlib import asynccontextmanager

from ratelimit.bucket import TokenBucket


class _Request:
    __slots__ = ("key", "seq", "granted", "wake")

    def __init__(self, key, seq):
        self.key = key
        self.seq = seq
        self.granted = False
        self.wake = asyncio.Event()


class RateLimiter:
    def __init__(self, rate, burst, max_concurrent, *, clock, sleep):
        if not isinstance(rate, (int, float)) or isinstance(rate, bool) or not rate > 0:
            raise ValueError("rate must be a number > 0")
        if not isinstance(burst, int) or isinstance(burst, bool) or burst < 1:
            raise ValueError("burst must be an int >= 1")
        if not isinstance(max_concurrent, int) or isinstance(max_concurrent, bool) or max_concurrent < 1:
            raise ValueError("max_concurrent must be an int >= 1")
        self._rate = rate
        self._burst = burst
        self._max = max_concurrent
        self._clock = clock
        self._sleep = sleep
        self._buckets = {}
        self._queues = {}
        self._in_use = 0
        self._seq = itertools.count()

    # -- state helpers -------------------------------------------------

    def _bucket(self, key):
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = self._buckets[key] = TokenBucket(self._rate, self._burst, self._clock)
        return bucket

    def _heads(self):
        return {key: queue[0] for key, queue in self._queues.items() if queue}

    def _remove(self, request):
        queue = self._queues[request.key]
        queue.remove(request)
        if not queue:
            del self._queues[request.key]

    def _grant_pass(self, before=None):
        if before is None:
            before = self._heads()
        while self._in_use < self._max:
            eligible = [req for req in self._heads().values() if self._bucket(req.key).available() >= 1]
            if not eligible:
                break
            request = min(eligible, key=lambda req: req.seq)
            self._bucket(request.key).try_take()
            self._remove(request)
            self._in_use += 1
            request.granted = True
            request.wake.set()
        for key, head in self._heads().items():
            if before.get(key) is not head:
                head.wake.set()  # new head: let it start waiting for a token

    # -- public API ----------------------------------------------------

    async def acquire(self, key):
        """Wait until a request for `key` is granted (one token and one slot)."""
        request = _Request(key, next(self._seq))
        self._bucket(key)
        self._queues.setdefault(key, deque()).append(request)
        self._grant_pass()
        if request.granted:
            return
        try:
            while not request.granted:
                request.wake.clear()
                queue = self._queues.get(key)
                is_head = queue is not None and queue[0] is request
                delay = self._bucket(key).time_until_available() if is_head else 0.0
                if is_head and delay > 0:
                    await self._sleep_or_wake(request, delay)
                    self._grant_pass()
                else:
                    await request.wake.wait()
        except asyncio.CancelledError:
            before = self._heads()
            if request.granted:
                self._in_use -= 1
                self._bucket(key).put_back()
            else:
                self._remove(request)
            self._grant_pass(before)
            raise

    async def _sleep_or_wake(self, request, delay):
        sleeper = asyncio.ensure_future(self._sleep(delay))
        waker = asyncio.ensure_future(request.wake.wait())
        try:
            await asyncio.wait({sleeper, waker}, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in (sleeper, waker):
                if not task.done():
                    task.cancel()

    def release(self):
        """Free one slot."""
        if self._in_use == 0:
            raise RuntimeError("release() called with no slot held")
        self._in_use -= 1
        self._grant_pass()

    @asynccontextmanager
    async def limit(self, key):
        """Async context manager: acquire on entry, release on exit."""
        await self.acquire(key)
        try:
            yield
        finally:
            self.release()

    @property
    def in_use(self):
        return self._in_use

    def tokens(self, key):
        bucket = self._buckets.get(key)
        return float(self._burst) if bucket is None else bucket.available()

    def waiting(self, key=None):
        if key is None:
            return sum(len(queue) for queue in self._queues.values())
        return len(self._queues.get(key, ()))
