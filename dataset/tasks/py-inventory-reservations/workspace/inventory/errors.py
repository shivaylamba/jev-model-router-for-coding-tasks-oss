"""Inventory errors."""


class InventoryError(Exception):
    """Base class for reservation errors."""


class InsufficientStockError(InventoryError):
    pass


class HoldNotFoundError(InventoryError, KeyError):
    pass


class HoldExpiredError(InventoryError):
    pass


class HoldStateError(InventoryError):
    """The hold is in a state that does not allow this operation."""


class IdempotencyConflictError(InventoryError):
    """A request id was reused for a different reservation."""
