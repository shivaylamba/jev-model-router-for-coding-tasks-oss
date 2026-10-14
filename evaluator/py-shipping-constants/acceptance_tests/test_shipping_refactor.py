import unittest
import warnings
from unittest import mock

import orders
import shipping

# Values produced by the original calc().
CASES = [
    ((1, 1), 6.24),
    ((0.2, 1), 5.62),
    ((1.2, 2), 7.62),
    ((3, 3), 12.12),
    ((2, 3, True), 14.61),
    ((40, 3, True), 75.0),
    ((60, 3), 75.0),
]


class ShippingCostTest(unittest.TestCase):
    def test_same_results_as_before(self):
        for args, expected in CASES:
            with self.subTest(args=args):
                self.assertEqual(shipping.shipping_cost(*args), expected)

    def test_keyword_express(self):
        self.assertEqual(shipping.shipping_cost(2, 3, express=True), 14.61)

    def test_errors_unchanged(self):
        for args in [(0, 1), (-1, 2), (1, 0), (1, 4)]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    shipping.shipping_cost(*args)

    def test_constants(self):
        self.assertEqual(shipping.BASE_FEE, 4.99)
        self.assertEqual(shipping.PER_KG_RATE, 1.25)
        self.assertEqual(shipping.WEIGHT_STEP_KG, 0.5)
        self.assertEqual(shipping.ZONE_MULTIPLIERS, {1: 1.0, 2: 1.4, 3: 1.9})
        self.assertEqual(shipping.EXPRESS_MULTIPLIER, 1.5)
        self.assertEqual(shipping.MAX_COST, 75.0)

    def test_constants_are_used(self):
        with mock.patch.object(shipping, "BASE_FEE", 0.0):
            self.assertEqual(shipping.shipping_cost(1, 1), 1.25)
        with mock.patch.object(shipping, "MAX_COST", 10.0):
            self.assertEqual(shipping.shipping_cost(5, 3), 10.0)
        with mock.patch.object(shipping, "EXPRESS_MULTIPLIER", 2.0):
            self.assertEqual(shipping.shipping_cost(1, 1, express=True), 12.48)
        with mock.patch.dict(shipping.ZONE_MULTIPLIERS, {2: 2.0}):
            self.assertEqual(shipping.shipping_cost(1, 2), 7.49)


class DeprecatedAliasTest(unittest.TestCase):
    def test_calc_warns_and_matches(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = shipping.calc(1.2, 2)
        self.assertEqual(result, 7.62)
        self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))

    def test_calc_express_keyword(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.assertEqual(shipping.calc(2, 3, express=True), 14.61)

    def test_shipping_cost_does_not_warn(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            self.assertEqual(shipping.shipping_cost(1, 1), 6.24)


class OrdersTest(unittest.TestCase):
    def test_orders_use_new_name(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            self.assertEqual(orders.order_shipping([1, 1.2], 2), 14.36)
            self.assertEqual(orders.parcel_costs([1, 2], 3, express=True), [11.05, 14.61])


if __name__ == "__main__":
    unittest.main()
