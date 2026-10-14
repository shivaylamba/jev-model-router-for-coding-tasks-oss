import unittest

from kv import format_kv


class FormatKvTest(unittest.TestCase):
    def test_format(self):
        self.assertEqual(format_kv({"a": 1, "b": "two"}), "a=1; b=two")

    def test_empty(self):
        self.assertEqual(format_kv({}), "")


if __name__ == "__main__":
    unittest.main()
