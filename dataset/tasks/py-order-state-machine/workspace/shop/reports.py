"""Dashboard summaries."""

from collections import Counter


def status_counts(orders):
    """Number of orders in each status, as a plain dict."""
    return dict(Counter(order.status for order in orders))


def open_value_cents(orders):
    """Value of orders that are paid but not yet shipped."""
    return sum(order.total_cents() for order in orders if order.status in ("paid", "packed"))
