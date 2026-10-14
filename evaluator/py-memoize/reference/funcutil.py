"""Function decorators."""

import functools
from typing import NamedTuple


def once(func):
    """Call `func` the first time only; later calls return the first result."""
    result = []

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not result:
            result.append(func(*args, **kwargs))
        return result[0]

    return wrapper


class CacheInfo(NamedTuple):
    hits: int
    misses: int
    size: int


def memoize(func):
    """Cache results by arguments. Adds cache_info() and cache_clear() to the wrapper."""
    cache = {}
    stats = {"hits": 0, "misses": 0}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        hash(key)
        if key in cache:
            stats["hits"] += 1
            return cache[key]
        stats["misses"] += 1
        value = func(*args, **kwargs)
        cache[key] = value
        return value

    def cache_info():
        return CacheInfo(stats["hits"], stats["misses"], len(cache))

    def cache_clear():
        cache.clear()
        stats["hits"] = stats["misses"] = 0

    wrapper.cache_info = cache_info
    wrapper.cache_clear = cache_clear
    return wrapper
