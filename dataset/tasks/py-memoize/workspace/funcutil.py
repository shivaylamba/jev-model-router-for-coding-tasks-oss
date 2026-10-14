"""Function decorators."""

import functools


def once(func):
    """Call `func` the first time only; later calls return the first result."""
    result = []

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not result:
            result.append(func(*args, **kwargs))
        return result[0]

    return wrapper
