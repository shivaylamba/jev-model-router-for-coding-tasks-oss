"""Re-engagement emails."""

from datetime import timedelta

from stats import get_user_stats

QUIET_PERIOD = timedelta(days=14)


def should_send_reengagement(events, user_id, now):
    """Email users who were active on at least 2 days but have been quiet for 14 days or more."""
    stats = get_user_stats(events, user_id)
    if stats[2] is None or stats[1] < 2:
        return False
    return now - stats[2] >= QUIET_PERIOD
