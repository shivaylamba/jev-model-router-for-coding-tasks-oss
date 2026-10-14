import unittest
from sensors import average_reading

class T(unittest.TestCase):
    def test_all(self):
        self.assertEqual(average_reading([1, 2, 3]), 2)
    def test_none_skipped(self):
        self.assertEqual(average_reading([None, 4, None, 6]), 5)
    def test_last_counts(self):
        self.assertEqual(average_reading([2, 10]), 6)
    def test_empty(self):
        self.assertIsNone(average_reading([]))
    def test_all_none(self):
        self.assertIsNone(average_reading([None, None]))
