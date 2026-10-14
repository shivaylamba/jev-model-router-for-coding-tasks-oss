import datetime
import unittest

from timesheets.report import build_report, paginate_rows, weekly_totals
from timesheets.weeks import week_key

D = datetime.date


class WeekKeyTest(unittest.TestCase):
    def test_days_belonging_to_previous_iso_year(self):
        self.assertEqual(week_key(D(2021, 1, 1)), "2020-W53")
        self.assertEqual(week_key(D(2021, 1, 3)), "2020-W53")
        self.assertEqual(week_key(D(2021, 1, 4)), "2021-W01")

    def test_days_belonging_to_next_iso_year(self):
        self.assertEqual(week_key(D(2024, 12, 30)), "2025-W01")
        self.assertEqual(week_key(D(2025, 1, 1)), "2025-W01")
        self.assertEqual(week_key(D(2025, 12, 29)), "2026-W01")
        self.assertEqual(week_key(D(2025, 12, 28)), "2025-W52")

    def test_mid_year_numbering(self):
        self.assertEqual(week_key(D(2025, 3, 10)), "2025-W11")
        self.assertEqual(week_key(D(2025, 3, 16)), "2025-W11")
        self.assertEqual(week_key(D(2026, 1, 5)), "2026-W02")

    def test_no_week_zero(self):
        for offset in range(0, 3 * 366):
            key = week_key(D(2025, 1, 1) + datetime.timedelta(days=offset))
            self.assertNotEqual(key[-2:], "00", key)


class WeeklyTotalsTest(unittest.TestCase):
    def test_new_year_week_is_one_row(self):
        entries = [
            (D(2024, 12, 27), 2.0),
            (D(2024, 12, 30), 8.0),
            (D(2024, 12, 31), 4.0),
            (D(2025, 1, 1), 1.5),
            (D(2025, 1, 6), 3.0),
        ]
        self.assertEqual(
            weekly_totals(entries),
            [("2024-W52", 2.0), ("2025-W01", 13.5), ("2025-W02", 3.0)],
        )

    def test_sorted_across_years(self):
        entries = [(D(2021, 1, 4), 1.0), (D(2021, 1, 2), 2.0), (D(2020, 12, 21), 3.0)]
        self.assertEqual(
            weekly_totals(entries),
            [("2020-W52", 3.0), ("2020-W53", 2.0), ("2021-W01", 1.0)],
        )


class PaginateRowsTest(unittest.TestCase):
    def test_partial_last_page(self):
        rows = list(range(10))
        self.assertEqual(paginate_rows(rows, 4), [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]])

    def test_exact_multiple(self):
        self.assertEqual(paginate_rows(list(range(8)), 4), [[0, 1, 2, 3], [4, 5, 6, 7]])

    def test_fewer_rows_than_a_page(self):
        self.assertEqual(paginate_rows([1, 2, 3], 4), [[1, 2, 3]])

    def test_no_rows(self):
        self.assertEqual(paginate_rows([], 4), [])

    def test_page_size_one(self):
        self.assertEqual(paginate_rows(["a", "b"], 1), [["a"], ["b"]])

    def test_invalid_page_size(self):
        with self.assertRaises(ValueError):
            paginate_rows([1], 0)


class BuildReportTest(unittest.TestCase):
    def test_every_week_is_on_a_page(self):
        start = D(2025, 11, 3)
        entries = [(start + datetime.timedelta(weeks=i), 1.0 + i) for i in range(10)]
        report = build_report(entries, per_page=4)
        self.assertEqual(report["weeks"], 10)
        self.assertEqual([len(page) for page in report["pages"]], [4, 4, 2])
        flat = [row for page in report["pages"] for row in page]
        self.assertEqual(sum(hours for _, hours in flat), report["total_hours"])
        self.assertEqual(flat[-1], ("2026-W02", 10.0))
        self.assertEqual(flat[8], ("2026-W01", 9.0))


if __name__ == "__main__":
    unittest.main()
