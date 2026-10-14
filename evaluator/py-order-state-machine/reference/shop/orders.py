"""Orders and their lifecycle (see docs/ORDER_LIFECYCLE.md)."""

from datetime import datetime, timedelta, timezone
from typing import NamedTuple

REFUND_WINDOW = timedelta(days=30)
TERMINAL_STATES = frozenset({"cancelled", "refunded"})

TRANSITIONS = {
    "pay": ({"pending"}, "paid"),
    "pack": ({"paid"}, "packed"),
    "ship": ({"packed"}, "shipped"),
    "deliver": ({"shipped"}, "delivered"),
    "cancel": ({"pending", "paid", "packed"}, "cancelled"),
    "refund": ({"paid", "packed", "delivered"}, "refunded"),
}


class InvalidTransition(Exception):
    """An event is not allowed in the order's current state."""

    def __init__(self, state, event):
        super().__init__(f"cannot {event} an order that is {state}")
        self.state = state
        self.event = event


class Transition(NamedTuple):
    event: str
    from_state: str
    to_state: str
    at: datetime


def _utc_now():
    return datetime.now(timezone.utc)


def _required_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


class Order:
    """A customer order.

    `items` is a list of (sku, quantity, unit_price_cents) tuples. `clock` is a
    zero-argument callable returning the current datetime.
    """

    def __init__(self, order_id, items, clock=None):
        self.order_id = order_id
        self.items = list(items)
        self.status = "pending"
        self.tracking_number = None
        self.cancel_reason = None
        self.delivered_at = None
        self.history = []
        self._clock = clock or _utc_now

    def total_cents(self):
        return sum(quantity * price for _sku, quantity, price in self.items)

    @property
    def is_terminal(self):
        return self.status in TERMINAL_STATES

    def can(self, event):
        rule = TRANSITIONS.get(event)
        if rule is None or self.status not in rule[0]:
            return False
        if event == "refund" and self.status == "delivered":
            return self._clock() - self.delivered_at <= REFUND_WINDOW
        return True

    def allowed_events(self):
        return sorted(event for event in TRANSITIONS if self.can(event))

    def _check(self, event):
        if not self.can(event):
            raise InvalidTransition(self.status, event)

    def _move(self, event):
        at = self._clock()
        target = TRANSITIONS[event][1]
        self.history.append(Transition(event, self.status, target, at))
        self.status = target
        return at

    def pay(self):
        self._check("pay")
        self._move("pay")

    def pack(self):
        self._check("pack")
        self._move("pack")

    def ship(self, tracking_number):
        self._check("ship")
        tracking_number = _required_text(tracking_number, "tracking number")
        self.tracking_number = tracking_number
        self._move("ship")

    def deliver(self):
        self._check("deliver")
        self.delivered_at = self._move("deliver")

    def cancel(self, reason):
        self._check("cancel")
        reason = _required_text(reason, "reason")
        self.cancel_reason = reason
        self._move("cancel")

    def refund(self):
        self._check("refund")
        self._move("refund")
