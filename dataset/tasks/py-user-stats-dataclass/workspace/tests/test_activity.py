import unittest
from datetime import datetime, timezone

from dashboard import most_active, render_row
from emailer import should_send_reengagement
from events import Event
from stats import get_user_stats


def at(day, hour=12):
    return datetime(2026, 3, day, hour, tzinfo=timezone.utc)


EVENTS = [
    Event("ana", "login", at(1, 9)),
    Event("ana", "view", at(1, 10)),
    Event("ana", "view", at(3)),
    Event("bo", "login", at(2)),
]


class StatsTest(unittest.TestCase):
    def test_unpack(self):
        total, days, last = get_user_stats(EVENTS, "ana")
        self.assertEqual((total, days, last), (3, 2, at(3)))

    def test_unknown_user(self):
        total, days, last = get_user_stats(EVENTS, "zed")
        self.assertEqual((total, days, last), (0, 0, None))


class CallersTest(unittest.TestCase):
    def test_render_row(self):
        self.assertEqual(render_row(EVENTS, "ana"), "ana: 3 events on 2 days, last seen 2026-03-03")
        self.assertEqual(render_row(EVENTS, "zed"), "zed: 0 events on 0 days, last seen never")

    def test_most_active(self):
        self.assertEqual(most_active(EVENTS), ["ana", "bo"])

    def test_reengagement(self):
        self.assertTrue(should_send_reengagement(EVENTS, "ana", at(17)))
        self.assertFalse(should_send_reengagement(EVENTS, "ana", at(16)))
        self.assertFalse(should_send_reengagement(EVENTS, "bo", at(30)))


if __name__ == "__main__":
    unittest.main()
