"""Helpers for `key=value; key=value` strings."""


def format_kv(pairs):
    """Format a mapping as `key=value; key=value`, in the mapping's order.

    >>> format_kv({"region": "eu-west", "replicas": 3})
    'region=eu-west; replicas=3'
    """
    return "; ".join(f"{key}={value}" for key, value in pairs.items())
