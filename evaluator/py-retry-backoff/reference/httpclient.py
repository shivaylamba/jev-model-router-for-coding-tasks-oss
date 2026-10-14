"""Fetch JSON documents through a transport.

A transport is any object with a `get(url) -> str` method that returns the
response body or raises one of the errors in errors.py.
"""

import json
import time

from errors import TransientError
from retry import retry


def fetch_json(transport, url, sleep=time.sleep):
    """Return the decoded JSON body at `url`, retrying transient failures."""
    body = retry(lambda: transport.get(url), attempts=4, base_delay=0.5, max_delay=4.0,
                 retry_on=TransientError, sleep=sleep)
    return json.loads(body)
