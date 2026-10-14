"""Week helpers. Finance reports by ISO 8601 week."""

import datetime


def week_key(day):
    """Return the ISO 8601 week key of `day` as 'YYYY-Www'.

    YYYY is the ISO week-numbering year and ww the ISO week number (01 to 53),
    zero-padded. ISO weeks start on Monday, and week 01 is the week containing
    the year's first Thursday, so a few days around New Year belong to a week
    of the neighbouring year. Keys sort chronologically as strings.
    """
    return day.strftime("%Y-W%W")


def week_start(day):
    """Return the Monday of the week containing `day`."""
    return day - datetime.timedelta(days=day.weekday())
