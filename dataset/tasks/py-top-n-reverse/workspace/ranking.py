"""Ranking helpers."""


def top_n(items, n, key=None):
    """Return the n largest items, largest first.

    `key` works like the key argument of sorted(). Items that compare equal
    keep their original relative order. If n is larger than the number of
    items, all items are returned. The input is never modified.
    """
    return sorted(items, key=key, reverse=True)[:n]


def rank_positions(scores):
    """Map each score to its 1-based competition rank ("1224" ranking)."""
    ordered = sorted(scores, reverse=True)
    positions = {}
    for index, score in enumerate(ordered, start=1):
        positions.setdefault(score, index)
    return positions
