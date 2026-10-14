"""Card and bank-account helpers for the checkout service."""

from iban_countries import IBAN_LENGTHS  # noqa: F401  (used by the IBAN check)


def strip_separators(text, separators=" -"):
    """Return text with every character in `separators` removed."""
    return "".join(ch for ch in text if ch not in separators)


def mask_card(number):
    """Mask all but the last four digits: '4111 1111 1111 1111' -> '************1111'.

    Spaces and hyphens are ignored. Raises ValueError if fewer than four digits remain.
    """
    digits = strip_separators(number)
    if len(digits) < 4 or not digits.isdigit():
        raise ValueError("not a card number")
    return "*" * (len(digits) - 4) + digits[-4:]
