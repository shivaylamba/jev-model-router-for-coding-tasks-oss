import unittest

from inventory.clock import ManualClock
from inventory.errors import (HoldExpiredError, HoldNotFoundError, HoldStateError, IdempotencyConflictError,
                              InsufficientStockError)
from inventory.service import ReservationService
from inventory.stock import StockLedger


class Base(unittest.TestCase):
    def setUp(self):
        self.clock = ManualClock(1000)
        self.ledger = StockLedger({"mug": 5, "lamp": 2})
        self.service = ReservationService(self.ledger, self.clock, hold_ttl=600)


class ExpiryTest(Base):
    def test_expired_holds_stop_counting_without_a_sweep(self):
        self.service.reserve("mug", 4, "cart-1")
        self.assertEqual(self.service.available("mug"), 1)
        self.clock.advance(600)
        self.assertEqual(self.service.available("mug"), 5)

    def test_expiry_boundary(self):
        hold = self.service.reserve("mug", 1, "cart-1")
        self.clock.advance(599.5)
        self.assertEqual(self.service.get_hold(hold.id).status, "held")
        self.assertEqual(self.service.available("mug"), 4)
        self.clock.advance(0.5)
        self.assertEqual(self.service.get_hold(hold.id).status, "expired")
        self.assertEqual(self.service.available("mug"), 5)

    def test_stock_freed_by_expiry_can_be_reserved(self):
        self.service.reserve("lamp", 2, "cart-1")
        with self.assertRaises(InsufficientStockError):
            self.service.reserve("lamp", 1, "cart-2")
        self.clock.advance(600)
        hold = self.service.reserve("lamp", 2, "cart-3")
        self.assertEqual(hold.status, "held")
        self.assertEqual(self.service.available("lamp"), 0)

    def test_sweep_makes_no_difference(self):
        a = self.service.reserve("mug", 2, "cart-1")
        self.clock.advance(300)
        self.service.reserve("mug", 1, "cart-2")
        self.clock.advance(300)  # a expired, b still held
        before = self.service.available("mug")
        self.assertEqual(self.service.get_hold(a.id).status, "expired")
        self.service.sweep_expired()
        self.service.sweep_expired()
        self.assertEqual(before, 4)
        self.assertEqual(self.service.available("mug"), 4)
        self.assertFalse(self.service.release(a.id))
        self.assertEqual(self.service.available("mug"), 4)

    def test_sweep_returns_number_marked(self):
        self.service.reserve("mug", 1, "cart-1")
        self.service.reserve("mug", 1, "cart-2")
        self.clock.advance(600)
        self.assertEqual(self.service.sweep_expired(), 2)


class ReleaseTest(Base):
    def test_double_release(self):
        hold = self.service.reserve("mug", 3, "cart-1")
        self.assertTrue(self.service.release(hold.id))
        self.assertFalse(self.service.release(hold.id))
        self.assertEqual(self.service.available("mug"), 5)
        self.assertEqual(self.service.get_hold(hold.id).status, "released")

    def test_double_release_does_not_allow_overselling(self):
        first = self.service.reserve("lamp", 2, "cart-1")
        self.service.release(first.id)
        self.service.release(first.id)
        self.service.reserve("lamp", 2, "cart-2")
        with self.assertRaises(InsufficientStockError):
            self.service.reserve("lamp", 1, "cart-3")

    def test_release_after_confirm(self):
        hold = self.service.reserve("mug", 2, "cart-1")
        self.service.confirm(hold.id)
        with self.assertRaises(HoldStateError):
            self.service.release(hold.id)
        self.assertEqual(self.ledger.on_hand("mug"), 3)
        self.assertEqual(self.service.available("mug"), 3)
        self.assertEqual(self.service.get_hold(hold.id).status, "confirmed")

    def test_unknown_hold(self):
        with self.assertRaises(HoldNotFoundError):
            self.service.release("h999")
        with self.assertRaises(HoldNotFoundError):
            self.service.confirm("h999")


class ConfirmTest(Base):
    def test_confirm_after_expiry_is_refused(self):
        hold = self.service.reserve("mug", 2, "cart-1")
        self.clock.advance(600)
        with self.assertRaises(HoldExpiredError):
            self.service.confirm(hold.id)
        self.assertEqual(self.ledger.on_hand("mug"), 5)
        self.assertEqual(self.service.available("mug"), 5)
        self.assertEqual(self.service.get_hold(hold.id).status, "expired")

    def test_double_confirm(self):
        hold = self.service.reserve("mug", 2, "cart-1")
        first = self.service.confirm(hold.id)
        second = self.service.confirm(hold.id)
        self.assertEqual(first.id, second.id)
        self.assertEqual(second.status, "confirmed")
        self.assertEqual(self.ledger.on_hand("mug"), 3)
        self.assertEqual(self.service.available("mug"), 3)

    def test_confirm_stays_confirmed_after_ttl(self):
        hold = self.service.reserve("mug", 1, "cart-1")
        self.service.confirm(hold.id)
        self.clock.advance(10_000)
        self.assertEqual(self.service.get_hold(hold.id).status, "confirmed")
        self.assertEqual(self.service.confirm(hold.id).status, "confirmed")
        self.assertEqual(self.ledger.on_hand("mug"), 4)

    def test_confirm_released(self):
        hold = self.service.reserve("mug", 1, "cart-1")
        self.service.release(hold.id)
        with self.assertRaises(HoldStateError):
            self.service.confirm(hold.id)
        self.assertEqual(self.ledger.on_hand("mug"), 5)


class IdempotencyTest(Base):
    def test_retry_returns_same_hold(self):
        first = self.service.reserve("mug", 2, "req-42")
        second = self.service.reserve("mug", 2, "req-42")
        self.assertEqual(first.id, second.id)
        self.assertEqual(self.service.available("mug"), 3)

    def test_retry_does_not_fail_when_stock_is_now_short(self):
        first = self.service.reserve("lamp", 2, "req-1")
        again = self.service.reserve("lamp", 2, "req-1")
        self.assertEqual(again.id, first.id)

    def test_retry_with_different_parameters(self):
        self.service.reserve("mug", 2, "req-42")
        with self.assertRaises(IdempotencyConflictError):
            self.service.reserve("mug", 3, "req-42")
        with self.assertRaises(IdempotencyConflictError):
            self.service.reserve("lamp", 2, "req-42")
        self.assertEqual(self.service.available("mug"), 3)
        self.assertEqual(self.service.available("lamp"), 2)

    def test_retry_after_expiry_returns_expired_hold(self):
        first = self.service.reserve("mug", 2, "req-7")
        self.clock.advance(600)
        again = self.service.reserve("mug", 2, "req-7")
        self.assertEqual(again.id, first.id)
        self.assertEqual(again.status, "expired")
        self.assertEqual(self.service.available("mug"), 5)

    def test_retry_after_confirm(self):
        first = self.service.reserve("mug", 2, "req-8")
        self.service.confirm(first.id)
        again = self.service.reserve("mug", 2, "req-8")
        self.assertEqual(again.id, first.id)
        self.assertEqual(again.status, "confirmed")
        self.assertEqual(self.ledger.on_hand("mug"), 3)

    def test_failed_reservation_is_not_remembered(self):
        with self.assertRaises(InsufficientStockError):
            self.service.reserve("lamp", 3, "req-9")
        self.ledger.restock("lamp", 1)
        hold = self.service.reserve("lamp", 3, "req-9")
        self.assertEqual(hold.status, "held")
        self.assertEqual(self.service.available("lamp"), 0)

    def test_distinct_requests_get_distinct_holds(self):
        a = self.service.reserve("mug", 1, "req-a")
        b = self.service.reserve("mug", 1, "req-b")
        self.assertNotEqual(a.id, b.id)
        self.assertEqual(self.service.available("mug"), 3)

    def test_validation(self):
        for bad in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                self.service.reserve("mug", bad, "req-v")
        with self.assertRaises(ValueError):
            self.service.reserve("mug", 1, "")
