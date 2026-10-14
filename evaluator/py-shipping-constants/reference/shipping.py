"""Shipping prices for a single parcel."""

import math
import warnings

BASE_FEE = 4.99
PER_KG_RATE = 1.25
WEIGHT_STEP_KG = 0.5
ZONE_MULTIPLIERS = {1: 1.0, 2: 1.4, 3: 1.9}
EXPRESS_MULTIPLIER = 1.5
MAX_COST = 75.0


def shipping_cost(weight_kg, zone, express=False):
    """Return the shipping cost in dollars for one parcel.

    The weight is rounded up to the next WEIGHT_STEP_KG before pricing.
    Zones are 1 (local), 2 (regional) and 3 (national). Express
    delivery costs extra, and no parcel costs more than MAX_COST.

    Raises ValueError for a weight that is not positive or an unknown zone.
    """
    if weight_kg <= 0:
        raise ValueError("weight must be positive")
    if zone not in ZONE_MULTIPLIERS:
        raise ValueError(f"unknown zone {zone!r}")
    billable = math.ceil(weight_kg / WEIGHT_STEP_KG) * WEIGHT_STEP_KG
    cost = BASE_FEE + billable * PER_KG_RATE * ZONE_MULTIPLIERS[zone]
    if express:
        cost = cost * EXPRESS_MULTIPLIER
    if cost > MAX_COST:
        cost = MAX_COST
    return round(cost, 2)


def calc(weight_kg, zone, express=False):
    """Deprecated: use shipping_cost()."""
    warnings.warn("calc() is deprecated; use shipping_cost()", DeprecationWarning, stacklevel=2)
    return shipping_cost(weight_kg, zone, express)
