"""Username helpers."""

RESERVED = frozenset({"admin", "root", "support", "moderator"})


def normalize_username(raw):
    """Trim surrounding whitespace and lowercase a username as typed at signup."""
    return raw.strip().lower()


def is_reserved(name):
    """Whether a (normalized) username is reserved for staff accounts."""
    return name in RESERVED
