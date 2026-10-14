import io
import os
import unittest

from reports.cli import main
from reports.exporters import UnknownFormatError, format_names, get_exporter
from reports.model import load_report

EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "examples", "sales.json")


class ExporterTest(unittest.TestCase):
    def test_text(self):
        out = get_exporter("text").export(load_report(EXAMPLE))
        self.assertIn("North            1,204  98,213.50  yes", out)

    def test_markdown(self):
        out = get_exporter("markdown").export(load_report(EXAMPLE))
        self.assertIn("| West | 0 | - | - |", out)

    def test_unknown(self):
        with self.assertRaises(UnknownFormatError):
            get_exporter("pdf")


class CliTest(unittest.TestCase):
    def test_default_text(self):
        buf = io.StringIO()
        self.assertEqual(main([EXAMPLE], stdout=buf), 0)
        self.assertTrue(buf.getvalue().startswith("Q3 sales\n"))

    def test_list_formats(self):
        buf = io.StringIO()
        self.assertEqual(main(["--list-formats"], stdout=buf), 0)
        self.assertEqual(buf.getvalue().split(), format_names())


if __name__ == "__main__":
    unittest.main()
