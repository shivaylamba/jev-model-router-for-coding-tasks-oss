# ratelimit

Rate limiting for the outbound webhook dispatcher. `TokenBucket` is the
synchronous bucket the old worker uses; `RateLimiter` is the asyncio limiter
the new dispatcher needs (see `SPEC.md`).

Standard library only (Python 3.11). Nothing here reads the real time: the
clock and the sleep function are always passed in, so tests drive time with
the fake in `tests/fake_time.py`.

Run the tests with `python3 -m unittest discover -s tests -t .`
