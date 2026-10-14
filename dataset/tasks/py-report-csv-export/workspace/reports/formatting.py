"""Display formatting for the human-readable exporters."""


def display_value(value):
    """Format a cell for people: thousands separators, two decimals for floats, yes/no, '-' for null."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def is_numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)
