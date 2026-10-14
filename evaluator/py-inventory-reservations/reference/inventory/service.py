"""Reservation service used by checkout."""

from .errors import (HoldExpiredError, HoldNotFoundError, HoldStateError, IdempotencyConflictError,
                     InsufficientStockError)
from .holds import HoldStore


class ReservationService:
    def __init__(self, ledger, clock, hold_ttl=900):
        self._ledger = ledger
        self._clock = clock
        self._ttl = hold_ttl
        self._holds = HoldStore()

    def _refresh(self, hold, now=None):
        """Turn a held hold whose time is up into an expired one."""
        if hold.status == "held" and hold.is_expired(self._clock.now() if now is None else now):
            hold.status = "expired"
        return hold

    def _reserved(self, sku):
        now = self._clock.now()
        return sum(h.quantity for h in self._holds.all()
                   if h.sku == sku and self._refresh(h, now).status == "held")

    def available(self, sku):
        return self._ledger.on_hand(sku) - self._reserved(sku)

    def reserve(self, sku, quantity, request_id):
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            raise ValueError("quantity must be a positive integer")
        if not isinstance(request_id, str) or not request_id:
            raise ValueError("request_id must be a non-empty string")
        existing = self._holds.by_request(request_id)
        if existing is not None:
            if (existing.sku, existing.quantity) != (sku, quantity):
                raise IdempotencyConflictError(request_id)
            return self._refresh(existing)
        available = self.available(sku)
        if quantity > available:
            raise InsufficientStockError(f"only {available} of {sku} available")
        now = self._clock.now()
        return self._holds.create(sku, quantity, request_id, now, now + self._ttl)

    def get_hold(self, hold_id):
        hold = self._holds.get(hold_id)
        if hold is None:
            raise HoldNotFoundError(hold_id)
        return self._refresh(hold)

    def release(self, hold_id):
        hold = self.get_hold(hold_id)
        if hold.status == "confirmed":
            raise HoldStateError(f"hold {hold_id} is already confirmed")
        if hold.status != "held":
            return False
        hold.status = "released"
        return True

    def confirm(self, hold_id):
        hold = self.get_hold(hold_id)
        if hold.status == "confirmed":
            return hold
        if hold.status == "expired":
            raise HoldExpiredError(f"hold {hold_id} expired")
        if hold.status == "released":
            raise HoldStateError(f"hold {hold_id} was released")
        self._ledger.remove(hold.sku, hold.quantity)
        hold.status = "confirmed"
        return hold

    def sweep_expired(self):
        """Mark expired holds. Housekeeping only; availability never depends on it."""
        now = self._clock.now()
        marked = 0
        for hold in self._holds.all():
            if hold.status == "held" and hold.is_expired(now):
                hold.status = "expired"
                marked += 1
        return marked
