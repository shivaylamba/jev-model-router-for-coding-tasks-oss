import io
import json
import os
import tempfile
import unittest

from reports.cli import main
from reports.exporters import format_names, get_exporter
from reports.model import Column, Report

SALES = {
    "title": "Q3 sales",
    "columns": [
        {"key": "region", "label": "Region"},
        {"key": "orders", "label": "Orders"},
        {"key": "revenue", "label": "Revenue"},
        {"key": "target_met", "label": "Target met"},
    ],
    "rows": [
        {"region": "North", "orders": 1204, "revenue": 98213.5, "target_met": True},
        {"region": "South, coastal", "orders": 87, "revenue": 4410.0, "target_met": False},
        {"region": "West", "orders": 0, "revenue": None},
    ],
}

SALES_CSV = (
    "Region,Orders,Revenue,Target met\n"
    "North,1204,98213.50,true\n"
    '"South, coastal",87,4410.00,false\n'
    "West,0,,\n"
)


def report(columns, rows, title="t"):
    return Report(title=title, columns=[Column(k, k) for k in columns], rows=rows)


class CsvExporterTest(unittest.TestCase):
    def setUp(self):
        self.exporter = get_exporter("csv")

    def test_registered(self):
        self.assertEqual(self.exporter.name, "csv")
        self.assertEqual(self.exporter.extension, ".csv")
        self.assertIn("csv", format_names())

    def test_sales_example(self):
        from reports.model import report_from_dict

        self.assertEqual(self.exporter.export(report_from_dict(SALES)), SALES_CSV)

    def test_integers_have_no_separators(self):
        out = self.exporter.export(report(["n"], [{"n": 1234567}, {"n": -42}]))
        self.assertEqual(out, "n\n1234567\n-42\n")

    def test_floats_two_decimals(self):
        out = self.exporter.export(report(["x"], [{"x": 1234567.891}, {"x": -0.5}, {"x": 3.0}, {"x": 0.125}]))
        self.assertEqual(out, "x\n1234567.89\n-0.50\n3.00\n0.12\n")

    def test_booleans_and_nulls(self):
        out = self.exporter.export(report(["a", "b", "c"], [{"a": True, "b": False, "c": None}, {}]))
        self.assertEqual(out, "a,b,c\ntrue,false,\n,,\n")

    def test_quoting(self):
        rows = [{"s": 'say "hi"'}, {"s": "two\nlines"}, {"s": "a,b"}, {"s": " padded "}, {"s": "007"}]
        out = self.exporter.export(report(["s"], rows))
        self.assertEqual(out, 's\n"say ""hi"""\n"two\nlines"\n"a,b"\n padded \n007\n')

    def test_header_labels_quoted_too(self):
        r = Report(title="t", columns=[Column("a", "Price, EUR"), Column("b", "Qty")], rows=[{"a": 1.5, "b": 2}])
        self.assertEqual(self.exporter.export(r), '"Price, EUR",Qty\n1.50,2\n')

    def test_no_carriage_returns_and_no_title(self):
        from reports.model import report_from_dict

        out = self.exporter.export(report_from_dict(SALES))
        self.assertNotIn("\r", out)
        self.assertNotIn("Q3 sales", out)

    def test_empty_report_is_header_only(self):
        self.assertEqual(self.exporter.export(report(["a", "b"], [])), "a,b\n")


class CsvCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "sales.json")
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(SALES, handle)

    def tearDown(self):
        self.tmp.cleanup()

    def test_stdout(self):
        buf = io.StringIO()
        self.assertEqual(main(["--format", "csv", self.path], stdout=buf), 0)
        self.assertEqual(buf.getvalue(), SALES_CSV)

    def test_output_file(self):
        target = os.path.join(self.tmp.name, "out.csv")
        self.assertEqual(main(["--format", "csv", "--output", target, self.path], stdout=io.StringIO()), 0)
        with open(target, "rb") as handle:
            self.assertEqual(handle.read().decode("utf-8"), SALES_CSV)

    def test_list_formats(self):
        buf = io.StringIO()
        self.assertEqual(main(["--list-formats"], stdout=buf), 0)
        self.assertEqual(buf.getvalue(), "csv\nmarkdown\ntext\n")

    def test_existing_formats_unchanged(self):
        buf = io.StringIO()
        self.assertEqual(main(["--format", "markdown", self.path], stdout=buf), 0)
        self.assertIn("| North | 1,204 | 98,213.50 | yes |", buf.getvalue())
