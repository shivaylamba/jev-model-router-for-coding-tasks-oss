import unittest
from textstats import word_counts

class T(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(word_counts("a b a"), {"a": 2, "b": 1})
    def test_case(self):
        self.assertEqual(word_counts("The the THE"), {"the": 3})
    def test_apostrophe(self):
        self.assertEqual(word_counts("don't stop"), {"don't": 1, "stop": 1})
    def test_punctuation(self):
        self.assertEqual(word_counts("x,y;x"), {"x": 2, "y": 1})
    def test_empty(self):
        self.assertEqual(word_counts(""), {})
