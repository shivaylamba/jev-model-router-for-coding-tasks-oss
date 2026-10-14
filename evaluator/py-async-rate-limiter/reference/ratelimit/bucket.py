"""A synchronous token bucket with an injected clock."""


class TokenBucket:
    """Holds up to `burst` tokens and gains `rate` tokens per second of clock time."""

    def __init__(self, rate, burst, clock):
        if rate <= 0:
            raise ValueError("rate must be positive")
        if burst < 1:
            raise ValueError("burst must be at least 1")
        self.rate = rate
        self.burst = burst
        self._clock = clock
        self._tokens = float(burst)
        self._updated = clock()

    def _refill(self):
        now = self._clock()
        elapsed = now - self._updated
        if elapsed > 0:
            self._tokens = min(float(self.burst), self._tokens + elapsed * self.rate)
        self._updated = now

    def available(self):
        """Current number of tokens (a float)."""
        self._refill()
        return self._tokens

    def try_take(self):
        """Take one token if there is one; return whether a token was taken."""
        self._refill()
        if self._tokens >= 1:
            self._tokens -= 1
            return True
        return False

    def time_until_available(self):
        """Seconds until at least one token is available (0.0 if one is available now)."""
        self._refill()
        if self._tokens >= 1:
            return 0.0
        return (1 - self._tokens) / self.rate

    def put_back(self):
        """Return one token taken earlier (never above `burst`)."""
        self._refill()
        self._tokens = min(float(self.burst), self._tokens + 1)
