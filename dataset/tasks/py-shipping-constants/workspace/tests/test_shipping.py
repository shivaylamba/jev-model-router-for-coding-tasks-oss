import unittest

import orders
import shipping


class ShippingTest(unittest.TestCase):
    def test_zone_one(self):
        self.assertEqual(shipping.calc(1, 1), 6.24)

    def test_weight_rounds_up_to_half_kilo(self):
        self.assertEqual(shipping.calc(1.2, 2), 7.62)

    def test_express(self):
        self.assertEqual(shipping.calc(2, 3, express=True), 14.61)

    def test_cap(self):
        self.assertEqual(shipping.calc(40, 3, express=True), 75.0)

    def test_errors(self):
        with self.assertRaises(ValueError):
            shipping.calc(0, 1)
        with self.assertRaises(ValueError):
            shipping.calc(1, 4)


class OrdersTest(unittest.TestCase):
    def test_order_shipping(self):
        self.assertEqual(orders.order_shipping([1, 1.2], 2), 14.36)


if __name__ == "__main__":
    unittest.main()
