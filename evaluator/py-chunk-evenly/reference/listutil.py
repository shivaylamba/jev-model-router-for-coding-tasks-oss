"""List helpers."""


def flatten(nested):
    """Flatten one level of nesting: [[1, 2], [3]] -> [1, 2, 3]."""
    return [item for group in nested for item in group]


def chunk_evenly(items, n):
    """Split items into n consecutive chunks whose sizes differ by at most one, longer first."""
    if n < 1:
        raise ValueError("n must be at least 1")
    size, extra = divmod(len(items), n)
    chunks, start = [], 0
    for index in range(n):
        end = start + size + (1 if index < extra else 0)
        chunks.append(list(items[start:end]))
        start = end
    return chunks
