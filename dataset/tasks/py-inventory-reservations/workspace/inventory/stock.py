"""Units physically on hand."""

from collections import defaultdict

from .errors import InsufficientStockError


class StockLedger:
    def __init__(self, initial=None):
        self._on_hand = defaultdict(int)
        for sku, units in (initial or {}).items():
            self.restock(sku, units)

    def on_hand(self, sku):
        return self._on_hand.get(sku, 0)

    def restock(self, sku, units):
        if units < 0:
            raise ValueError("units must not be negative")
        self._on_hand[sku] += units

    def remove(self, sku, units):
        if units > self.on_hand(sku):
            raise InsufficientStockError(f"only {self.on_hand(sku)} of {sku} on hand")
        self._on_hand[sku] -= units
