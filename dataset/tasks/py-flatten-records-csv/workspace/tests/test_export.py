import unittest

from csvexport import rows_to_csv
from loader import parse_ndjson


class LoaderTest(unittest.TestCase):
    def test_parse_ndjson(self):
        self.assertEqual(parse_ndjson('{"a": 1}\n\n{"a": 2}\n'), [{"a": 1}, {"a": 2}])

    def test_bad_line(self):
        with self.assertRaises(ValueError):
            parse_ndjson('{"a": 1}\nnope\n')


class RowsToCsvTest(unittest.TestCase):
    def test_rows_to_csv(self):
        self.assertEqual(rows_to_csv(["a", "b"], [["1", "x,y"]]), 'a,b\r\n1,"x,y"\r\n')


if __name__ == "__main__":
    unittest.main()
