"""GitHub-flavoured Markdown table."""

from ..formatting import display_value, is_numeric


def _escape(text):
    return text.replace("|", "\\|")


class MarkdownExporter:
    name = "markdown"
    extension = ".md"

    def export(self, report):
        numeric = [any(is_numeric(report.cell(row, c)) for row in report.rows) for c in report.columns]
        lines = [f"## {report.title}", ""]
        lines.append("| " + " | ".join(_escape(c.label) for c in report.columns) + " |")
        lines.append("|" + "|".join("---:" if n else "---" for n in numeric) + "|")
        for row in report.rows:
            cells = [_escape(display_value(report.cell(row, c))) for c in report.columns]
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines) + "\n"
