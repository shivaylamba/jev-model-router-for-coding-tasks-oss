import unittest

from listutil import flatten


class FlattenTest(unittest.TestCase):
    def test_flatten(self):
        self.assertEqual(flatten([[1, 2], [], [3]]), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
