"""List helpers."""


def flatten(nested):
    """Flatten one level of nesting: [[1, 2], [3]] -> [1, 2, 3]."""
    return [item for group in nested for item in group]
