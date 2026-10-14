"""CSV output for exported events."""

import csv
import io


def rows_to_csv(header, rows):
    """Render a header and rows (lists of strings) with the csv module's default dialect."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


def _scalar(value):
    if value is None:
        return ""
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def _cell(value):
    if isinstance(value, (list, tuple)):
        return ";".join(_scalar(item) for item in value)
    return _scalar(value)


def _flatten(record, prefix, out):
    for key, value in record.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            _flatten(value, path + ".", out)
            continue
        if path in out:
            raise ValueError(f"column {path!r} appears twice in one record")
        out[path] = _cell(value)


def records_to_csv(records):
    """Flatten a list of (possibly nested) dicts into CSV text."""
    flat_rows = []
    columns = {}
    for record in records:
        if not isinstance(record, dict):
            raise TypeError(f"records must be dicts, got {type(record).__name__}")
        flat = {}
        _flatten(record, "", flat)
        for path in flat:
            columns.setdefault(path, None)
        flat_rows.append(flat)
    if not flat_rows:
        return ""
    header = list(columns)
    return rows_to_csv(header, [[flat.get(col, "") for col in header] for flat in flat_rows])
