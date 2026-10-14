"""Re-engagement emails."""

from datetime import timedelta

from stats import get_user_stats

QUIET_PERIOD = timedelta(days=14)


def should_send_reengagement(events, user_id, now):
    """Email users who were active on at least 2 days but have been quiet for 14 days or more."""
    stats = get_user_stats(events, user_id)
    if stats.last_seen is None or stats.active_days < 2:
        return False
    return now - stats.last_seen >= QUIET_PERIOD
