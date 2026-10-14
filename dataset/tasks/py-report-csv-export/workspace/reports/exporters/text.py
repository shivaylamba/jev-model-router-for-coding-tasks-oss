"""Plain text table."""

from ..formatting import display_value, is_numeric


class TextExporter:
    name = "text"
    extension = ".txt"

    def export(self, report):
        header = [column.label for column in report.columns]
        body = [[display_value(report.cell(row, c)) for c in report.columns] for row in report.rows]
        numeric = [any(is_numeric(report.cell(row, c)) for row in report.rows) for c in report.columns]
        widths = [max([len(header[i])] + [len(line[i]) for line in body]) for i in range(len(header))]

        def fmt(cells):
            parts = [cell.rjust(widths[i]) if numeric[i] else cell.ljust(widths[i]) for i, cell in enumerate(cells)]
            return "  ".join(parts).rstrip()

        lines = [report.title, "", fmt(header), "  ".join("-" * w for w in widths)]
        lines += [fmt(line) for line in body]
        return "\n".join(lines) + "\n"
