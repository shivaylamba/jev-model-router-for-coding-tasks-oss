"""Parsing the time-tracking CSV export."""

import csv
import datetime
import io


def parse_entries(text):
    """Parse 'date,hours' CSV text (with a header row) into [(date, float)]."""
    reader = csv.DictReader(io.StringIO(text))
    entries = []
    for row in reader:
        day = datetime.date.fromisoformat(row["date"].strip())
        entries.append((day, float(row["hours"])))
    return entries
