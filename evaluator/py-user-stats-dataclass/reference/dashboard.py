"""Rows for the admin dashboard."""

from stats import get_all_user_stats, get_user_stats


def render_row(events, user_id):
    stats = get_user_stats(events, user_id)
    seen = stats.last_seen.strftime("%Y-%m-%d") if stats.last_seen else "never"
    return f"{user_id}: {stats.total_events} events on {stats.active_days} days, last seen {seen}"


def most_active(events, limit=3):
    """User ids with the most events, most first; ties by user id."""
    all_stats = get_all_user_stats(events)
    ranked = sorted(all_stats.items(), key=lambda item: (-item[1].total_events, item[0]))
    return [user_id for user_id, _ in ranked[:limit]]
