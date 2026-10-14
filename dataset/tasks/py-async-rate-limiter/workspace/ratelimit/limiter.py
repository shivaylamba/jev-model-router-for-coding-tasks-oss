"""Asyncio rate limiter: per-key token buckets plus a global concurrency cap.

See SPEC.md for the full behaviour.
"""


class RateLimiter:
    def __init__(self, rate, burst, max_concurrent, *, clock, sleep):
        raise NotImplementedError

    async def acquire(self, key):
        """Wait until a request for `key` is granted (one token and one slot)."""
        raise NotImplementedError

    def release(self):
        """Free one slot."""
        raise NotImplementedError

    def limit(self, key):
        """Async context manager: acquire on entry, release on exit."""
        raise NotImplementedError

    @property
    def in_use(self):
        raise NotImplementedError

    def tokens(self, key):
        raise NotImplementedError

    def waiting(self, key=None):
        raise NotImplementedError
