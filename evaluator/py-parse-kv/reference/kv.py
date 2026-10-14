"""Helpers for `key=value; key=value` strings."""


def format_kv(pairs):
    """Format a mapping as `key=value; key=value`, in the mapping's order.

    >>> format_kv({"region": "eu-west", "replicas": 3})
    'region=eu-west; replicas=3'
    """
    return "; ".join(f"{key}={value}" for key, value in pairs.items())


def parse_kv(text):
    """Parse `key=value; key=value` into a dict of strings."""
    result = {}
    for segment in text.split(";"):
        if not segment.strip():
            continue
        if "=" not in segment:
            raise ValueError(f"segment without '=': {segment!r}")
        key, value = segment.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"empty key in segment {segment!r}")
        result[key] = value.strip()
    return result
