"""Retry a callable with capped exponential backoff."""

import functools
import time


def retry(fn, *, attempts=3, base_delay=0.1, max_delay=5.0, retry_on=(Exception,),
          sleep=time.sleep, on_retry=None):
    """Call fn() until it succeeds, at most `attempts` times in total."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if base_delay < 0 or max_delay < 0:
        raise ValueError("delays must not be negative")
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except retry_on as exc:
            if attempt == attempts:
                raise
            delay = min(max_delay, base_delay * 2 ** (attempt - 1))
            if on_retry is not None:
                on_retry(attempt, exc, delay)
            sleep(delay)
    raise AssertionError("unreachable")


def retrying(**options):
    """Decorator form of retry(); the options are the keyword arguments of retry()."""
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return retry(lambda: func(*args, **kwargs), **options)
        return wrapper
    return decorate
