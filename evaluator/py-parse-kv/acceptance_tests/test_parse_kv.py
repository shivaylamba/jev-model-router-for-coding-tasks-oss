import unittest

from kv import format_kv, parse_kv


class ParseKvTest(unittest.TestCase):
    def test_example(self):
        self.assertEqual(parse_kv("a=1; b = two"), {"a": "1", "b": "two"})

    def test_values_are_strings_and_trimmed(self):
        self.assertEqual(parse_kv("  region =  eu-west  ;replicas=3"), {"region": "eu-west", "replicas": "3"})

    def test_empty_segments_skipped(self):
        self.assertEqual(parse_kv("a=1;; ;b=2;"), {"a": "1", "b": "2"})

    def test_empty_input(self):
        self.assertEqual(parse_kv(""), {})
        self.assertEqual(parse_kv("  ;  "), {})

    def test_last_duplicate_wins(self):
        result = parse_kv("a=1; b=2; a=3")
        self.assertEqual(result, {"a": "3", "b": "2"})

    def test_split_on_first_equals(self):
        self.assertEqual(parse_kv("query=x=1&y=2"), {"query": "x=1&y=2"})

    def test_empty_value_allowed(self):
        self.assertEqual(parse_kv("a=; b=2"), {"a": "", "b": "2"})

    def test_segment_without_equals(self):
        with self.assertRaises(ValueError):
            parse_kv("a=1; oops; b=2")

    def test_empty_key(self):
        with self.assertRaises(ValueError):
            parse_kv("a=1; = 2")

    def test_round_trip(self):
        self.assertEqual(parse_kv(format_kv({"x": "1", "y": "z"})), {"x": "1", "y": "z"})
