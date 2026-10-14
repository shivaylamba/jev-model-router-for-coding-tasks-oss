"""Per-user activity statistics."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UserStats:
    """One user's activity summary.

    Unpacks, indexes and has len() like the (total_events, active_days,
    last_seen) tuple that get_user_stats used to return.
    """

    total_events: int
    active_days: int
    last_seen: datetime | None

    def __iter__(self):
        return iter((self.total_events, self.active_days, self.last_seen))

    def __len__(self):
        return 3

    def __getitem__(self, index):
        return (self.total_events, self.active_days, self.last_seen)[index]

    @property
    def events_per_active_day(self):
        if self.active_days == 0:
            return 0.0
        return self.total_events / self.active_days

    def as_dict(self):
        return {"total_events": self.total_events, "active_days": self.active_days, "last_seen": self.last_seen}


def get_user_stats(events, user_id):
    """Summarise one user's events as a UserStats.

    total_events is the number of events for the user, active_days the number
    of distinct UTC calendar dates with at least one event, and last_seen the
    latest event time, or None when the user has no events.
    """
    mine = [event for event in events if event.user_id == user_id]
    if not mine:
        return UserStats(0, 0, None)
    days = {event.at.date() for event in mine}
    return UserStats(len(mine), len(days), max(event.at for event in mine))


def get_all_user_stats(events):
    """get_user_stats for every user that appears in `events`, keyed by user id."""
    user_ids = sorted({event.user_id for event in events})
    return {user_id: get_user_stats(events, user_id) for user_id in user_ids}
