"""Formatting helpers for contact records."""


def format_name(first, last):
    """'ada', 'LOVELACE' -> 'Ada Lovelace'. Blank parts are skipped."""
    parts = [p.strip().capitalize() for p in (first, last) if p and p.strip()]
    return " ".join(parts)


def normalize_email(email):
    """Trim and lowercase an e-mail address."""
    return email.strip().lower()


_SEPARATORS = set(" ()-.+")


def format_us_phone(raw):
    """Format a US phone number as '(415) 555-0123'."""
    if any(not (ch.isdigit() or ch in _SEPARATORS) for ch in raw):
        raise ValueError(f"unexpected characters in phone number: {raw!r}")
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) == 11 and digits[0] == "1":
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError(f"not a 10-digit US phone number: {raw!r}")
    if digits[0] in "01" or digits[3] in "01":
        raise ValueError(f"area code and exchange cannot start with 0 or 1: {raw!r}")
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
