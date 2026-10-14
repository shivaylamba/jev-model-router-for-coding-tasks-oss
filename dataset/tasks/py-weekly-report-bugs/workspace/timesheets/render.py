"""Plain-text rendering of a report."""


def render(report):
    lines = [f"{report['weeks']} weeks, {report['total_hours']:.2f} hours"]
    count = len(report["pages"])
    for number, page in enumerate(report["pages"], start=1):
        lines.append(f"-- page {number}/{count} --")
        lines.extend(f"{key}  {hours:6.2f}" for key, hours in page)
    return "\n".join(lines)
