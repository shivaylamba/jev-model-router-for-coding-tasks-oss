import unittest
from datetime import datetime, timedelta, timezone

from cron import next_run
from jobs import Registry, plan


def dt(*args):
    return datetime(*args)


class BasicsTest(unittest.TestCase):
    def test_every_minute_drops_seconds(self):
        self.assertEqual(next_run("* * * * *", dt(2025, 10, 14, 10, 0, 30, 500)), dt(2025, 10, 14, 10, 1))

    def test_strictly_after(self):
        self.assertEqual(next_run("30 9 * * *", dt(2025, 10, 14, 9, 30)), dt(2025, 10, 15, 9, 30))
        self.assertEqual(next_run("30 9 * * *", dt(2025, 10, 14, 9, 29, 59)), dt(2025, 10, 14, 9, 30))

    def test_steps(self):
        self.assertEqual(next_run("*/15 * * * *", dt(2025, 10, 14, 10, 46)), dt(2025, 10, 14, 11, 0))
        self.assertEqual(next_run("5/20 * * * *", dt(2025, 10, 14, 10, 26)), dt(2025, 10, 14, 10, 45))
        self.assertEqual(next_run("0 9-17/4 * * *", dt(2025, 10, 14, 13, 0)), dt(2025, 10, 14, 17, 0))
        self.assertEqual(next_run("0 9-17/4 * * *", dt(2025, 10, 14, 17, 0)), dt(2025, 10, 15, 9, 0))

    def test_lists_and_ranges(self):
        self.assertEqual(next_run("10,40 8-9 * * *", dt(2025, 10, 14, 8, 40)), dt(2025, 10, 14, 9, 10))
        self.assertEqual(next_run("0 22 * * *", dt(2025, 12, 31, 23, 0)), dt(2026, 1, 1, 22, 0))

    def test_month_and_year_rollover(self):
        self.assertEqual(next_run("0 0 1 * *", dt(2025, 1, 31, 23, 59)), dt(2025, 2, 1, 0, 0))
        self.assertEqual(next_run("0 0 1 1 *", dt(2025, 6, 15)), dt(2026, 1, 1))
        self.assertEqual(next_run("0 0 31 * *", dt(2025, 4, 1)), dt(2025, 5, 31))

    def test_whitespace(self):
        self.assertEqual(next_run("  0\t9  * *   1 ", dt(2025, 10, 14)), dt(2025, 10, 20, 9, 0))

    def test_tzinfo_is_kept(self):
        tz = timezone(timedelta(hours=2))
        result = next_run("0 12 * * *", datetime(2025, 10, 14, 13, 0, tzinfo=tz))
        self.assertEqual(result, datetime(2025, 10, 15, 12, 0, tzinfo=tz))
        self.assertIs(result.tzinfo, tz)


class NamesTest(unittest.TestCase):
    def test_weekday_range_by_name(self):
        # 2025-10-17 is a Friday
        self.assertEqual(next_run("0 9 * * MON-FRI", dt(2025, 10, 17, 10, 0)), dt(2025, 10, 20, 9, 0))

    def test_names_are_case_insensitive(self):
        self.assertEqual(next_run("0 0 1 jan,Jul *", dt(2025, 2, 1)), dt(2025, 7, 1))
        self.assertEqual(next_run("0 9 * * sat", dt(2025, 10, 14)), dt(2025, 10, 18, 9, 0))

    def test_sunday_as_0_and_7(self):
        self.assertEqual(next_run("0 12 * * 0", dt(2025, 10, 14)), dt(2025, 10, 19, 12, 0))
        self.assertEqual(next_run("0 12 * * 7", dt(2025, 10, 14)), dt(2025, 10, 19, 12, 0))
        self.assertEqual(next_run("0 12 * * 5-7", dt(2025, 10, 18, 13, 0)), dt(2025, 10, 19, 12, 0))


class DayRuleTest(unittest.TestCase):
    def test_both_restricted_is_or(self):
        # 2025-10-17 is Friday; 2025-11-13 is a Thursday
        self.assertEqual(next_run("0 0 13 * FRI", dt(2025, 10, 14)), dt(2025, 10, 17))
        self.assertEqual(next_run("0 0 13 * FRI", dt(2025, 11, 8)), dt(2025, 11, 13))

    def test_star_step_day_of_month_is_and(self):
        # Mondays on odd days: 2025-10-20 is even, 2025-10-27 is odd
        self.assertEqual(next_run("0 0 */2 * MON", dt(2025, 10, 14)), dt(2025, 10, 27))

    def test_only_day_of_week_restricted(self):
        self.assertEqual(next_run("0 0 * * SUN", dt(2025, 10, 14)), dt(2025, 10, 19))

    def test_month_always_applies(self):
        self.assertEqual(next_run("0 0 1 MAR MON", dt(2025, 10, 14)), dt(2026, 3, 1))


class LeapYearTest(unittest.TestCase):
    def test_feb_29(self):
        self.assertEqual(next_run("0 0 29 2 *", dt(2025, 3, 1)), dt(2028, 2, 29))

    def test_2100_is_not_a_leap_year(self):
        self.assertEqual(next_run("0 0 29 2 *", dt(2096, 3, 1)), dt(2104, 2, 29))


class MacroTest(unittest.TestCase):
    def test_macros(self):
        after = dt(2025, 10, 14, 10, 30)  # a Tuesday
        self.assertEqual(next_run("@hourly", after), dt(2025, 10, 14, 11, 0))
        self.assertEqual(next_run("@daily", after), dt(2025, 10, 15))
        self.assertEqual(next_run("@midnight", after), dt(2025, 10, 15))
        self.assertEqual(next_run("@weekly", after), dt(2025, 10, 19))
        self.assertEqual(next_run("@monthly", after), dt(2025, 11, 1))
        self.assertEqual(next_run("@yearly", after), dt(2026, 1, 1))
        self.assertEqual(next_run(" @Annually ", after), dt(2026, 1, 1))


class ErrorTest(unittest.TestCase):
    def test_invalid_expressions(self):
        bad = [
            "* * * *",
            "* * * * * *",
            "",
            "@reboot",
            "60 * * * *",
            "* 24 * * *",
            "* * 0 * *",
            "* * 32 * *",
            "* * * 13 *",
            "* * * 0 *",
            "* * * * 8",
            "5-1 * * * *",
            "*/0 * * * *",
            "1,,2 * * * *",
            "1, * * * *",
            "abc * * * *",
            "* * * FOO *",
            "* * * * MON/2/3",
            "* * * */FEB *",
            "*/x * * * *",
            "-5 * * * *",
        ]
        for expr in bad:
            with self.subTest(expr=expr):
                with self.assertRaises(ValueError):
                    next_run(expr, dt(2025, 10, 14))

    def test_never_matching(self):
        for expr in ["0 0 30 2 *", "0 0 31 4,6,9,11 *"]:
            with self.subTest(expr=expr):
                with self.assertRaises(ValueError):
                    next_run(expr, dt(2025, 10, 14))


class PlanTest(unittest.TestCase):
    def test_plan_orders_jobs(self):
        reg = Registry()
        reg.add("weekly-report", "0 8 * * MON")
        reg.add("vacuum", "30 3 * * *")
        reg.add("backup", "30 3 * * *")
        upcoming = plan(reg, dt(2025, 10, 14, 12, 0))
        self.assertEqual([(when, job.name) for when, job in upcoming], [
            (dt(2025, 10, 15, 3, 30), "backup"),
            (dt(2025, 10, 15, 3, 30), "vacuum"),
            (dt(2025, 10, 20, 8, 0), "weekly-report"),
        ])
