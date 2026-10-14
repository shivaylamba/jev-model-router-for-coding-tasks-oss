import unittest
from datetime import datetime, timedelta, timezone

from shop.orders import InvalidTransition, Order, Transition

START = datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc)


class FakeClock:
    def __init__(self):
        self.now = START

    def __call__(self):
        return self.now

    def advance(self, **kwargs):
        self.now += timedelta(**kwargs)


def new_order(clock=None):
    return Order("A1", [("PEN", 2, 150)], clock=clock or FakeClock())


def delivered_order():
    clock = FakeClock()
    order = new_order(clock)
    order.pay()
    clock.advance(hours=1)
    order.pack()
    order.ship("1Z999")
    clock.advance(days=2)
    order.deliver()
    return order, clock


class TransitionTableTest(unittest.TestCase):
    def test_invalid_transitions_raise_with_state_and_event(self):
        order = new_order()
        with self.assertRaises(InvalidTransition) as ctx:
            order.ship("1Z999")
        self.assertEqual((ctx.exception.state, ctx.exception.event), ("pending", "ship"))
        for event in ("pack", "deliver"):
            with self.assertRaises(InvalidTransition):
                getattr(order, event)()

    def test_pay_twice(self):
        order = new_order()
        order.pay()
        with self.assertRaises(InvalidTransition) as ctx:
            order.pay()
        self.assertEqual(ctx.exception.state, "paid")
        self.assertTrue(issubclass(InvalidTransition, Exception))

    def test_shipped_cannot_be_cancelled_or_refunded(self):
        order = new_order()
        order.pay()
        order.pack()
        order.ship("1Z999")
        with self.assertRaises(InvalidTransition):
            order.cancel("too late")
        with self.assertRaises(InvalidTransition):
            order.refund()
        self.assertEqual(order.status, "shipped")
        self.assertIsNone(order.cancel_reason)

    def test_cancel_from_each_allowed_state(self):
        for steps in ([], ["pay"], ["pay", "pack"]):
            order = new_order()
            for step in steps:
                getattr(order, step)()
            order.cancel("  out of stock ")
            self.assertEqual(order.status, "cancelled")
            self.assertEqual(order.cancel_reason, "out of stock")

    def test_refund_before_shipping(self):
        order = new_order()
        order.pay()
        order.refund()
        self.assertEqual(order.status, "refunded")

    def test_terminal_states(self):
        cancelled = new_order()
        cancelled.cancel("dupe")
        refunded = new_order()
        refunded.pay()
        refunded.refund()
        for order in (cancelled, refunded):
            self.assertTrue(order.is_terminal)
            self.assertEqual(order.allowed_events(), [])
            for event in ("pay", "pack", "deliver", "refund"):
                with self.assertRaises(InvalidTransition):
                    getattr(order, event)()
            with self.assertRaises(InvalidTransition):
                order.cancel("again")
        self.assertFalse(new_order().is_terminal)
        self.assertFalse(delivered_order()[0].is_terminal)


class GuardTest(unittest.TestCase):
    def test_tracking_number_required(self):
        for bad in ("", "   ", None, 42):
            order = new_order()
            order.pay()
            order.pack()
            with self.assertRaises(ValueError):
                order.ship(bad)
            self.assertEqual(order.status, "packed")
            self.assertEqual(len(order.history), 2)
            self.assertIsNone(order.tracking_number)

    def test_tracking_number_stripped(self):
        order = new_order()
        order.pay()
        order.pack()
        order.ship(" 1Z999 ")
        self.assertEqual(order.tracking_number, "1Z999")

    def test_reason_required(self):
        order = new_order()
        with self.assertRaises(ValueError):
            order.cancel(" ")
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.history, [])

    def test_state_checked_before_arguments(self):
        order = new_order()
        with self.assertRaises(InvalidTransition):
            order.ship("")
        done = new_order()
        done.cancel("x")
        with self.assertRaises(InvalidTransition):
            done.cancel("")

    def test_refund_window_is_thirty_days_inclusive(self):
        order, clock = delivered_order()
        clock.advance(days=30)
        self.assertTrue(order.can("refund"))
        clock.advance(seconds=1)
        self.assertFalse(order.can("refund"))
        self.assertEqual(order.allowed_events(), [])
        with self.assertRaises(InvalidTransition) as ctx:
            order.refund()
        self.assertEqual((ctx.exception.state, ctx.exception.event), ("delivered", "refund"))
        self.assertEqual(order.status, "delivered")

    def test_refund_within_window(self):
        order, clock = delivered_order()
        clock.advance(days=29, hours=23)
        order.refund()
        self.assertEqual(order.status, "refunded")


class HistoryTest(unittest.TestCase):
    def test_history_records_each_transition_with_clock_time(self):
        order, clock = delivered_order()
        self.assertEqual(order.history, [
            Transition("pay", "pending", "paid", START),
            Transition("pack", "paid", "packed", START + timedelta(hours=1)),
            Transition("ship", "packed", "shipped", START + timedelta(hours=1)),
            Transition("deliver", "shipped", "delivered", START + timedelta(days=2, hours=1)),
        ])
        first = order.history[0]
        self.assertEqual((first.event, first.from_state, first.to_state, first.at), ("pay", "pending", "paid", START))
        self.assertEqual(order.delivered_at, START + timedelta(days=2, hours=1))

    def test_new_order_has_empty_history(self):
        order = new_order()
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.history, [])
        self.assertIsNone(order.delivered_at)

    def test_failed_transition_not_recorded(self):
        order = new_order()
        with self.assertRaises(InvalidTransition):
            order.deliver()
        self.assertEqual(order.history, [])

    def test_default_clock_is_aware_utc(self):
        order = Order("A9", [])
        order.pay()
        self.assertEqual(order.history[0].at.utcoffset(), timedelta(0))


class QueryTest(unittest.TestCase):
    def test_can_and_allowed_events(self):
        order = new_order()
        self.assertEqual(order.allowed_events(), ["cancel", "pay"])
        self.assertTrue(order.can("pay"))
        self.assertFalse(order.can("ship"))
        self.assertFalse(order.can("teleport"))
        order.pay()
        self.assertEqual(order.allowed_events(), ["cancel", "pack", "refund"])
        order.pack()
        order.ship("1Z")
        self.assertEqual(order.allowed_events(), ["deliver"])
        order.deliver()
        self.assertEqual(order.allowed_events(), ["refund"])


if __name__ == "__main__":
    unittest.main()
