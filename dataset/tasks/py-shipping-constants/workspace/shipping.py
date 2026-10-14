"""Shipping prices for a single parcel."""

import math


def calc(weight_kg, zone, express=False):
    """Return the shipping cost in dollars for one parcel.

    The weight is rounded up to the next half kilogram before pricing.
    Zones are 1 (local), 2 (regional) and 3 (national). Express
    delivery costs extra, and no parcel costs more than the cap.

    Raises ValueError for a weight that is not positive or an unknown zone.
    """
    if weight_kg <= 0:
        raise ValueError("weight must be positive")
    if zone not in (1, 2, 3):
        raise ValueError(f"unknown zone {zone!r}")
    billable = math.ceil(weight_kg / 0.5) * 0.5
    cost = 4.99 + billable * 1.25 * {1: 1.0, 2: 1.4, 3: 1.9}[zone]
    if express:
        cost = cost * 1.5
    if cost > 75.0:
        cost = 75.0
    return round(cost, 2)
