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
