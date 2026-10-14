import unittest

from latency import fastest, slowest
from leaderboard import Player, podium
from ranking import top_n


class TopNReverseTest(unittest.TestCase):
    def test_default_unchanged(self):
        self.assertEqual(top_n([4, 9, 1, 7], 2), [9, 7])
        self.assertEqual(top_n([4, 9, 1, 7], 2, reverse=False), [9, 7])

    def test_reverse_smallest_first(self):
        self.assertEqual(top_n([4, 9, 1, 7], 2, reverse=True), [1, 4])

    def test_reverse_with_key(self):
        self.assertEqual(top_n(["bb", "a", "ccc"], 2, key=len, reverse=True), ["a", "bb"])

    def test_key_still_positional(self):
        self.assertEqual(top_n(["bb", "a", "ccc"], 1, len), ["ccc"])

    def test_reverse_is_keyword_only(self):
        with self.assertRaises(TypeError):
            top_n([1, 2, 3], 2, None, True)

    def test_ties_keep_original_order(self):
        pairs = [("a", 1), ("b", 2), ("c", 1), ("d", 2)]
        self.assertEqual(top_n(pairs, 2, key=lambda p: p[1]), [("b", 2), ("d", 2)])
        self.assertEqual(top_n(pairs, 2, key=lambda p: p[1], reverse=True), [("a", 1), ("c", 1)])

    def test_n_larger_than_items(self):
        self.assertEqual(top_n([3, 1, 2], 10, reverse=True), [1, 2, 3])

    def test_zero(self):
        self.assertEqual(top_n([3, 1, 2], 0), [])
        self.assertEqual(top_n([3, 1, 2], 0, reverse=True), [])

    def test_negative_n(self):
        with self.assertRaises(ValueError):
            top_n([3, 1, 2], -1)
        with self.assertRaises(ValueError):
            top_n([3, 1, 2], -2, reverse=True)

    def test_input_not_modified(self):
        data = [5, 3, 8]
        top_n(data, 2, reverse=True)
        self.assertEqual(data, [5, 3, 8])

    def test_callers(self):
        players = [Player("ana", 12), Player("bo", 30), Player("cy", 18), Player("di", 2)]
        self.assertEqual([p.name for p in podium(players)], ["bo", "cy", "ana"])
        self.assertEqual(slowest([120, 40, 980, 300], count=2), [980, 300])
        self.assertEqual(fastest([120, 40, 980, 300], count=2), [40, 120])
