"""Order-level helpers."""

from shipping import shipping_cost


def parcel_costs(parcels, zone, express=False):
    """Shipping cost of each parcel, given as a list of weights in kg."""
    return [shipping_cost(weight, zone, express) for weight in parcels]


def order_shipping(parcels, zone, express=False):
    """Total shipping for an order made of several parcels, rounded to cents."""
    return round(sum(parcel_costs(parcels, zone, express)), 2)
