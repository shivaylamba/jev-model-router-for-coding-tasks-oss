"""Report data."""

import json
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Column:
    key: str
    label: str


@dataclass
class Report:
    title: str
    columns: list[Column]
    rows: list[dict] = field(default_factory=list)

    def cell(self, row, column):
        """The raw value of `column` in `row`; a missing key is None."""
        return row.get(column.key)


def report_from_dict(data):
    columns = [Column(c["key"], c.get("label", c["key"])) for c in data["columns"]]
    return Report(title=data.get("title", ""), columns=columns, rows=list(data.get("rows", [])))


def load_report(path):
    with open(path, encoding="utf-8") as handle:
        return report_from_dict(json.load(handle))
