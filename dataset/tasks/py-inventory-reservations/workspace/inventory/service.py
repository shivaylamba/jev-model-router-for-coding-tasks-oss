"""Reservation service used by checkout."""

from collections import defaultdict

from .errors import (HoldNotFoundError, HoldStateError, IdempotencyConflictError,
                     InsufficientStockError)
from .holds import HoldStore


class ReservationService:
    def __init__(self, ledger, clock, hold_ttl=900):
        self._ledger = ledger
        self._clock = clock
        self._ttl = hold_ttl
        self._holds = HoldStore()
        self._reserved = defaultdict(int)

    def available(self, sku):
        return self._ledger.on_hand(sku) - self._reserved[sku]

    def reserve(self, sku, quantity, request_id):
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            raise ValueError("quantity must be a positive integer")
        if not isinstance(request_id, str) or not request_id:
            raise ValueError("request_id must be a non-empty string")
        existing = self._holds.by_request(request_id)
        if existing is not None:
            if (existing.sku, existing.quantity) != (sku, quantity):
                raise IdempotencyConflictError(request_id)
            return existing
        if quantity > self.available(sku):
            raise InsufficientStockError(f"only {self.available(sku)} of {sku} available")
        now = self._clock.now()
        hold = self._holds.create(sku, quantity, request_id, now, now + self._ttl)
        self._reserved[sku] += quantity
        return hold

    def get_hold(self, hold_id):
        hold = self._holds.get(hold_id)
        if hold is None:
            raise HoldNotFoundError(hold_id)
        return hold

    def release(self, hold_id):
        hold = self.get_hold(hold_id)
        hold.status = "released"
        self._reserved[hold.sku] -= hold.quantity
        return True

    def confirm(self, hold_id):
        hold = self.get_hold(hold_id)
        if hold.status == "released":
            raise HoldStateError(f"hold {hold_id} was released")
        self._ledger.remove(hold.sku, hold.quantity)
        self._reserved[hold.sku] -= hold.quantity
        hold.status = "confirmed"
        return hold

    def sweep_expired(self):
        """Mark expired holds and give their units back. Run by the nightly cleanup job."""
        now = self._clock.now()
        marked = 0
        for hold in self._holds.all():
            if hold.status == "held" and hold.is_expired(now):
                hold.status = "expired"
                self._reserved[hold.sku] -= hold.quantity
                marked += 1
        return marked
