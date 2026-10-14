"""Username helpers."""

RESERVED = frozenset({"admin", "root", "support", "moderator"})


def normalize_username(raw):
    """Trim surrounding whitespace and lowercase a username as typed at signup."""
    return raw.strip().lower()


def is_reserved(name):
    """Whether a (normalized) username is reserved for staff accounts."""
    return name in RESERVED


_LETTERS = "abcdefghijklmnopqrstuvwxyz"
_DIGITS = "0123456789"
_SEPARATORS = "._-"


def is_valid_username(name):
    """Whether `name` is an acceptable (already normalized) username."""
    if not isinstance(name, str) or not 3 <= len(name) <= 20:
        return False
    if name[0] not in _LETTERS:
        return False
    previous = ""
    for ch in name:
        if ch not in _LETTERS and ch not in _DIGITS and ch not in _SEPARATORS:
            return False
        if ch in _SEPARATORS and previous in _SEPARATORS and previous:
            return False
        previous = ch
    return name[-1] not in _SEPARATORS
