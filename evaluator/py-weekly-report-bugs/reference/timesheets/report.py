"""Weekly totals and report pages."""

from timesheets.weeks import week_key


def weekly_totals(entries):
    """Sum hours per ISO week.

    entries: iterable of (date, hours).
    Returns a list of (week_key, total_hours) tuples sorted by week key, one per
    week that has at least one entry, with totals rounded to 2 decimals.
    """
    totals = {}
    for day, hours in entries:
        key = week_key(day)
        totals[key] = totals.get(key, 0.0) + hours
    return [(key, round(total, 2)) for key, total in sorted(totals.items())]


def paginate_rows(rows, per_page):
    """Split rows into consecutive pages of `per_page` rows.

    Every row appears on exactly one page, in order. The last page may hold
    fewer than `per_page` rows. No rows gives no pages ([]).
    Raises ValueError if per_page < 1.
    """
    if per_page < 1:
        raise ValueError("per_page must be at least 1")
    pages = []
    for start in range(0, len(rows), per_page):
        pages.append(rows[start:start + per_page])
    return pages


def build_report(entries, per_page=4):
    """Build the report: {"weeks": int, "total_hours": float, "pages": [[(week_key, hours), ...], ...]}."""
    rows = weekly_totals(entries)
    return {
        "weeks": len(rows),
        "total_hours": round(sum(hours for _, hours in rows), 2),
        "pages": paginate_rows(rows, per_page),
    }
