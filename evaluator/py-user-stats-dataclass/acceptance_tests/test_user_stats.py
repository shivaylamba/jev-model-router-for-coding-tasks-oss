import dataclasses
import unittest
from datetime import datetime, timezone

from dashboard import most_active, render_row
from emailer import should_send_reengagement
from events import Event
from stats import UserStats, get_all_user_stats, get_user_stats


def at(day, hour=12):
    return datetime(2026, 3, day, hour, tzinfo=timezone.utc)


EVENTS = [
    Event("ana", "login", at(1, 9)),
    Event("ana", "view", at(1, 10)),
    Event("ana", "view", at(3)),
    Event("ana", "view", at(4)),
    Event("bo", "login", at(2)),
    Event("cy", "login", at(2)),
    Event("cy", "view", at(5)),
]


class UserStatsTest(unittest.TestCase):
    def test_returns_dataclass_with_fields(self):
        stats = get_user_stats(EVENTS, "ana")
        self.assertIsInstance(stats, UserStats)
        self.assertTrue(dataclasses.is_dataclass(stats))
        self.assertEqual(stats.total_events, 4)
        self.assertEqual(stats.active_days, 3)
        self.assertEqual(stats.last_seen, at(4))

    def test_field_order(self):
        self.assertEqual([f.name for f in dataclasses.fields(UserStats)], ["total_events", "active_days", "last_seen"])

    def test_unpacks_like_tuple(self):
        total, days, last = get_user_stats(EVENTS, "ana")
        self.assertEqual((total, days, last), (4, 3, at(4)))
        self.assertEqual(tuple(get_user_stats(EVENTS, "bo")), (1, 1, at(2)))

    def test_indexing_and_len(self):
        stats = get_user_stats(EVENTS, "ana")
        self.assertEqual(len(stats), 3)
        self.assertEqual(stats[0], 4)
        self.assertEqual(stats[1], 3)
        self.assertEqual(stats[-1], at(4))
        with self.assertRaises(IndexError):
            stats[3]

    def test_no_events(self):
        stats = get_user_stats(EVENTS, "zed")
        self.assertEqual(stats, UserStats(0, 0, None))
        self.assertEqual(stats.events_per_active_day, 0.0)

    def test_frozen(self):
        stats = get_user_stats(EVENTS, "ana")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            stats.total_events = 99

    def test_events_per_active_day(self):
        self.assertAlmostEqual(get_user_stats(EVENTS, "ana").events_per_active_day, 4 / 3)
        self.assertEqual(get_user_stats(EVENTS, "cy").events_per_active_day, 1.0)

    def test_as_dict(self):
        self.assertEqual(
            get_user_stats(EVENTS, "bo").as_dict(),
            {"total_events": 1, "active_days": 1, "last_seen": at(2)},
        )

    def test_get_all_user_stats(self):
        everything = get_all_user_stats(EVENTS)
        self.assertEqual(list(everything), ["ana", "bo", "cy"])
        self.assertTrue(all(isinstance(value, UserStats) for value in everything.values()))
        self.assertEqual(everything["cy"], UserStats(2, 2, at(5)))


class CallersTest(unittest.TestCase):
    def test_dashboard(self):
        self.assertEqual(render_row(EVENTS, "ana"), "ana: 4 events on 3 days, last seen 2026-03-04")
        self.assertEqual(render_row(EVENTS, "zed"), "zed: 0 events on 0 days, last seen never")
        self.assertEqual(most_active(EVENTS), ["ana", "cy", "bo"])

    def test_emailer(self):
        self.assertTrue(should_send_reengagement(EVENTS, "ana", at(18)))
        self.assertFalse(should_send_reengagement(EVENTS, "ana", at(17)))
        self.assertFalse(should_send_reengagement(EVENTS, "bo", at(30)))
        self.assertFalse(should_send_reengagement(EVENTS, "zed", at(30)))
