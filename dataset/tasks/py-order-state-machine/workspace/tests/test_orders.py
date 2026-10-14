import unittest

from shop.orders import Order
from shop.reports import open_value_cents, status_counts


class OrderTest(unittest.TestCase):
    def test_happy_path(self):
        order = Order("A1", [("PEN", 2, 150)])
        order.pay()
        order.pack()
        order.ship("1Z999")
        order.deliver()
        self.assertEqual(order.status, "delivered")
        self.assertEqual(order.tracking_number, "1Z999")

    def test_cancel(self):
        order = Order("A2", [])
        order.cancel("customer request")
        self.assertEqual(order.status, "cancelled")
        self.assertEqual(order.cancel_reason, "customer request")


class ReportsTest(unittest.TestCase):
    def test_counts_and_open_value(self):
        a = Order("A1", [("PEN", 2, 150)])
        b = Order("A2", [("INK", 1, 900)])
        c = Order("A3", [("PAD", 1, 400)])
        a.pay()
        b.pay()
        b.pack()
        self.assertEqual(status_counts([a, b, c]), {"paid": 1, "packed": 1, "pending": 1})
        self.assertEqual(open_value_cents([a, b, c]), 1200)


if __name__ == "__main__":
    unittest.main()
