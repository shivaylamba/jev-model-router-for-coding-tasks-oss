import unittest

from inventory.clock import ManualClock
from inventory.errors import InsufficientStockError
from inventory.service import ReservationService
from inventory.stock import StockLedger


class CheckoutFlowTest(unittest.TestCase):
    def setUp(self):
        self.clock = ManualClock(1000)
        self.ledger = StockLedger({"mug": 5})
        self.service = ReservationService(self.ledger, self.clock, hold_ttl=600)

    def test_reserve_and_confirm(self):
        hold = self.service.reserve("mug", 2, "cart-1")
        self.assertEqual(hold.status, "held")
        self.assertEqual(hold.expires_at, 1600)
        self.assertEqual(self.service.available("mug"), 3)
        self.service.confirm(hold.id)
        self.assertEqual(self.ledger.on_hand("mug"), 3)
        self.assertEqual(self.service.available("mug"), 3)

    def test_reserve_and_release(self):
        hold = self.service.reserve("mug", 4, "cart-2")
        self.assertTrue(self.service.release(hold.id))
        self.assertEqual(self.service.available("mug"), 5)

    def test_not_enough_stock(self):
        with self.assertRaises(InsufficientStockError):
            self.service.reserve("mug", 6, "cart-3")
        self.assertEqual(self.service.available("unknown-sku"), 0)


if __name__ == "__main__":
    unittest.main()
