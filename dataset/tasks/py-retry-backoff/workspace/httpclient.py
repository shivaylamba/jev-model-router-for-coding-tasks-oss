"""Fetch JSON documents through a transport.

A transport is any object with a `get(url) -> str` method that returns the
response body or raises one of the errors in errors.py.
"""

import json
import time

from errors import TransientError


def fetch_json(transport, url, sleep=time.sleep):
    """Return the decoded JSON body at `url`, retrying transient failures."""
    last = None
    for _ in range(3):
        try:
            return json.loads(transport.get(url))
        except TransientError as exc:
            last = exc
            sleep(1)
    raise last
