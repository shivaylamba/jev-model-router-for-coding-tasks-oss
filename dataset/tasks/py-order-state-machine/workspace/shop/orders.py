"""Orders and their lifecycle."""


class Order:
    """A customer order.

    `items` is a list of (sku, quantity, unit_price_cents) tuples.
    """

    def __init__(self, order_id, items):
        self.order_id = order_id
        self.items = list(items)
        self.status = "pending"
        self.tracking_number = None
        self.cancel_reason = None

    def total_cents(self):
        return sum(quantity * price for _sku, quantity, price in self.items)

    # TODO: none of these check the current status (see docs/ORDER_LIFECYCLE.md).

    def pay(self):
        self.status = "paid"

    def pack(self):
        self.status = "packed"

    def ship(self, tracking_number):
        self.tracking_number = tracking_number
        self.status = "shipped"

    def deliver(self):
        self.status = "delivered"

    def cancel(self, reason):
        self.cancel_reason = reason
        self.status = "cancelled"

    def refund(self):
        self.status = "refunded"
