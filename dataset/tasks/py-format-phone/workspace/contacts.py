"""Formatting helpers for contact records."""


def format_name(first, last):
    """'ada', 'LOVELACE' -> 'Ada Lovelace'. Blank parts are skipped."""
    parts = [p.strip().capitalize() for p in (first, last) if p and p.strip()]
    return " ".join(parts)


def normalize_email(email):
    """Trim and lowercase an e-mail address."""
    return email.strip().lower()
