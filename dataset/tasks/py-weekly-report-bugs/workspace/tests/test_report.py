import datetime
import unittest

from timesheets.entries import parse_entries
from timesheets.report import build_report, weekly_totals
from timesheets.weeks import week_start


class EntriesTest(unittest.TestCase):
    def test_parse(self):
        text = "date,hours\n2024-03-04,7.5\n2024-03-05, 8\n"
        self.assertEqual(
            parse_entries(text),
            [(datetime.date(2024, 3, 4), 7.5), (datetime.date(2024, 3, 5), 8.0)],
        )


class WeeksTest(unittest.TestCase):
    def test_week_start(self):
        self.assertEqual(week_start(datetime.date(2024, 3, 7)), datetime.date(2024, 3, 4))
        self.assertEqual(week_start(datetime.date(2024, 3, 4)), datetime.date(2024, 3, 4))


class ReportTest(unittest.TestCase):
    def test_weekly_totals_mid_year(self):
        entries = [
            (datetime.date(2024, 3, 4), 4.0),
            (datetime.date(2024, 3, 8), 3.5),
            (datetime.date(2024, 3, 11), 8.0),
        ]
        self.assertEqual(weekly_totals(entries), [("2024-W10", 7.5), ("2024-W11", 8.0)])

    def test_full_pages(self):
        entries = [(datetime.date(2024, 5, 6) + datetime.timedelta(weeks=i), 1.0) for i in range(4)]
        report = build_report(entries, per_page=2)
        self.assertEqual(len(report["pages"]), 2)
        self.assertEqual(report["total_hours"], 4.0)


if __name__ == "__main__":
    unittest.main()
