"""CSV for spreadsheets and scripts: machine-readable numbers, no display formatting."""

import csv
import io


def csv_value(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, ".2f")
    return str(value)


class CsvExporter:
    name = "csv"
    extension = ".csv"

    def export(self, report):
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        writer.writerow([column.label for column in report.columns])
        for row in report.rows:
            writer.writerow([csv_value(report.cell(row, column)) for column in report.columns])
        return buffer.getvalue()
