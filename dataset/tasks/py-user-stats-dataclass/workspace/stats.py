"""Per-user activity statistics."""


def get_user_stats(events, user_id):
    """Summarise one user's events.

    Returns a tuple (total_events, active_days, last_seen):
    total_events is the number of events for the user, active_days the number
    of distinct UTC calendar dates with at least one event, and last_seen the
    latest event time, or None when the user has no events.
    """
    mine = [event for event in events if event.user_id == user_id]
    if not mine:
        return (0, 0, None)
    days = {event.at.date() for event in mine}
    return (len(mine), len(days), max(event.at for event in mine))


def get_all_user_stats(events):
    """get_user_stats for every user that appears in `events`, keyed by user id."""
    user_ids = sorted({event.user_id for event in events})
    return {user_id: get_user_stats(events, user_id) for user_id in user_ids}
