import csv
import io
import unittest

from csvexport import records_to_csv


def parse(text):
    return list(csv.reader(io.StringIO(text, newline="")))


class RecordsToCsvTest(unittest.TestCase):
    def test_flat_records(self):
        self.assertEqual(records_to_csv([{"id": 1, "name": "ada"}, {"id": 2, "name": "bob"}]),
                         "id,name\r\n1,ada\r\n2,bob\r\n")

    def test_nested_dicts_become_dot_paths(self):
        rows = parse(records_to_csv([{"id": 7, "user": {"name": "ada", "geo": {"city": "London"}}, "ok": 1}]))
        self.assertEqual(rows[0], ["id", "user.name", "user.geo.city", "ok"])
        self.assertEqual(rows[1], ["7", "ada", "London", "1"])

    def test_first_seen_column_order_and_missing_cells(self):
        records = [
            {"id": 1, "user": {"name": "ada"}},
            {"id": 2, "tag": "x", "user": {"email": "b@x.io", "name": "bob"}},
            {"user": {"name": "cy"}, "id": 3},
        ]
        rows = parse(records_to_csv(records))
        self.assertEqual(rows[0], ["id", "user.name", "tag", "user.email"])
        self.assertEqual(rows[1], ["1", "ada", "", ""])
        self.assertEqual(rows[2], ["2", "bob", "x", "b@x.io"])
        self.assertEqual(rows[3], ["3", "cy", "", ""])

    def test_lists_are_joined(self):
        rows = parse(records_to_csv([{"tags": ["a", "b", 3], "ids": (1, 2), "none": [], "n": 0}]))
        self.assertEqual(rows[1], ["a;b;3", "1;2", "", "0"])

    def test_none_and_booleans(self):
        rows = parse(records_to_csv([{"a": None, "b": True, "c": False, "d": [True, None, False], "e": 1.5}]))
        self.assertEqual(rows[1], ["", "true", "false", "true;;false", "1.5"])

    def test_quoting(self):
        text = records_to_csv([{"note": 'say "hi", please', "multi": "line1\nline2", "plain": "x"}])
        self.assertEqual(text, 'note,multi,plain\r\n"say ""hi"", please","line1\nline2",x\r\n')

    def test_empty_nested_dict_adds_no_column(self):
        rows = parse(records_to_csv([{"id": 1, "meta": {}}, {"id": 2}]))
        self.assertEqual(rows, [["id"], ["1"], ["2"]])

    def test_scalar_and_nested_under_same_key_in_different_records(self):
        rows = parse(records_to_csv([{"a": 1}, {"a": {"b": 2}}]))
        self.assertEqual(rows, [["a", "a.b"], ["1", ""], ["", "2"]])

    def test_empty_input(self):
        self.assertEqual(records_to_csv([]), "")

    def test_collision_within_a_record(self):
        with self.assertRaises(ValueError):
            records_to_csv([{"a.b": 1, "a": {"b": 2}}])

    def test_non_dict_record(self):
        with self.assertRaises(TypeError):
            records_to_csv([{"a": 1}, ["not", "a", "dict"]])

    def test_input_not_modified(self):
        records = [{"user": {"name": "ada"}, "tags": ["x"]}]
        records_to_csv(records)
        self.assertEqual(records, [{"user": {"name": "ada"}, "tags": ["x"]}])
