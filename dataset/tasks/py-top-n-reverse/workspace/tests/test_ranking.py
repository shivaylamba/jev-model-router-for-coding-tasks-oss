import unittest

from latency import slowest
from leaderboard import Player, format_podium
from ranking import rank_positions, top_n


class TopNTest(unittest.TestCase):
    def test_largest_first(self):
        self.assertEqual(top_n([4, 9, 1, 7], 2), [9, 7])

    def test_key(self):
        self.assertEqual(top_n(["bb", "a", "ccc"], 2, key=len), ["ccc", "bb"])

    def test_more_than_available(self):
        self.assertEqual(top_n([3, 1], 5), [3, 1])

    def test_rank_positions(self):
        self.assertEqual(rank_positions([10, 20, 20, 5]), {20: 1, 10: 3, 5: 4})


class CallersTest(unittest.TestCase):
    def test_podium(self):
        players = [Player("ana", 12), Player("bo", 30), Player("cy", 18), Player("di", 2)]
        self.assertEqual(format_podium(players), "1. bo (30)\n2. cy (18)\n3. ana (12)")

    def test_slowest(self):
        self.assertEqual(slowest([120, 40, 980, 300], count=2), [980, 300])


if __name__ == "__main__":
    unittest.main()
