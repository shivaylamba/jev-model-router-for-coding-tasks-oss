"""Cron expression evaluation. The supported syntax is described in SPEC.md."""

from datetime import datetime


def next_run(expr: str, after: datetime) -> datetime:
    """The earliest minute strictly after `after` that matches `expr`."""
    raise NotImplementedError
