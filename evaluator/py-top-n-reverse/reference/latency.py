"""Latency summary for the ops report."""

from ranking import top_n


def slowest(timings_ms, count=5):
    """The `count` slowest request timings, slowest first."""
    return top_n(timings_ms, count)


def fastest(timings_ms, count=5):
    """The `count` fastest request timings, fastest first."""
    return top_n(timings_ms, count, reverse=True)
