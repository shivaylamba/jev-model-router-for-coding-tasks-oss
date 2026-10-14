"""Cron expression evaluation. The supported syntax is described in SPEC.md."""

import re
from datetime import date, datetime, timedelta

_MACROS = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}

_MONTHS = {n: i for i, n in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], start=1)}
_DAYS = {n: i for i, n in enumerate(["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"])}

# (minimum, maximum, names)
_FIELDS = [(0, 59, {}), (0, 23, {}), (1, 31, {}), (1, 12, _MONTHS), (0, 7, _DAYS)]

_SEARCH_DAYS = 8 * 366 + 2


def _value(text, lo, hi, names):
    if re.fullmatch(r"\d+", text):
        value = int(text)
    elif text.upper() in names:
        value = names[text.upper()]
    else:
        raise ValueError(f"invalid value {text!r}")
    if not lo <= value <= hi:
        raise ValueError(f"value {value} out of range {lo}-{hi}")
    return value


def _parse_field(text, lo, hi, names):
    values = set()
    for item in text.split(","):
        if not item:
            raise ValueError("empty item")
        base, slash, step_text = item.partition("/")
        if slash:
            if not re.fullmatch(r"\d+", step_text) or int(step_text) == 0:
                raise ValueError(f"invalid step {step_text!r}")
            step = int(step_text)
        else:
            step = 1
        if base == "*":
            start, end = lo, hi
        elif "-" in base:
            a, _, b = base.partition("-")
            start, end = _value(a, lo, hi, names), _value(b, lo, hi, names)
            if start > end:
                raise ValueError(f"range {base!r} runs backwards")
        else:
            start = _value(base, lo, hi, names)
            end = hi if slash else start
        values.update(range(start, end + 1, step))
    return values


def _parse(expr):
    text = expr.strip()
    if text.startswith("@"):
        if text.lower() not in _MACROS:
            raise ValueError(f"unknown macro {text!r}")
        text = _MACROS[text.lower()]
    fields = text.split()
    if len(fields) != 5:
        raise ValueError(f"expected 5 fields, got {len(fields)}")
    sets = [_parse_field(f, lo, hi, names) for f, (lo, hi, names) in zip(fields, _FIELDS)]
    dow = {d % 7 for d in sets[4]}
    dom_star = fields[2].startswith("*")
    dow_star = fields[4].startswith("*")
    return sets[0], sets[1], sets[2], sets[3], dow, dom_star or dow_star


def next_run(expr: str, after: datetime) -> datetime:
    """The earliest minute strictly after `after` that matches `expr`."""
    minutes, hours, doms, months, dows, both = _parse(expr)
    minutes, hours = sorted(minutes), sorted(hours)
    start = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    day = start.date()
    for _ in range(_SEARCH_DAYS):
        if day.month in months:
            dom_ok = day.day in doms
            dow_ok = (day.isoweekday() % 7) in dows
            if (dom_ok and dow_ok) if both else (dom_ok or dow_ok):
                first = (start.hour, start.minute) if day == start.date() else (0, 0)
                for h in hours:
                    if h < first[0]:
                        continue
                    for m in minutes:
                        if h == first[0] and m < first[1]:
                            continue
                        return datetime(day.year, day.month, day.day, h, m, tzinfo=after.tzinfo)
        day += timedelta(days=1)
    raise ValueError(f"{expr!r} has no matching time within eight years")
