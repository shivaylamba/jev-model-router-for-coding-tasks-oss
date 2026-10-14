"""Sensor helpers."""


def average_reading(readings):
    values = [r for r in readings if r is not None]
    if not values:
        return None
    return sum(values) / len(values)
