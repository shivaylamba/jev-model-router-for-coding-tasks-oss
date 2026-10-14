"""Read newline-delimited JSON."""

import json


def parse_ndjson(text):
    """Parse one JSON object per line; blank lines are skipped."""
    records = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {number}: {exc.msg}") from None
    return records
