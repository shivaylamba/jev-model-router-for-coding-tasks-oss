"""Job registry for the maintenance runner."""

import re
from dataclasses import dataclass
from datetime import datetime

_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,39}$")


@dataclass(frozen=True)
class Job:
    name: str
    schedule: str


class Registry:
    def __init__(self):
        self._jobs = {}

    def add(self, name, schedule):
        """Register a job. Names are lowercase identifiers and must be unique."""
        if not _NAME.match(name):
            raise ValueError(f"invalid job name {name!r}")
        if name in self._jobs:
            raise ValueError(f"duplicate job {name!r}")
        self._jobs[name] = Job(name, schedule)
        return self._jobs[name]

    def jobs(self):
        return list(self._jobs.values())


def plan(registry, after: datetime):
    """(next run time, job) pairs for every job, soonest first, ties by name."""
    from cron import next_run

    upcoming = [(next_run(job.schedule, after), job) for job in registry.jobs()]
    upcoming.sort(key=lambda pair: (pair[0], pair[1].name))
    return upcoming
