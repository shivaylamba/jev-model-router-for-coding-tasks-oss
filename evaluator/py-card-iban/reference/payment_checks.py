"""Card and bank-account helpers for the checkout service."""

from iban_countries import IBAN_LENGTHS


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


def _luhn_ok(digits):
    total = 0
    for index, ch in enumerate(reversed(digits)):
        value = int(ch)
        if index % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def _is_ascii_digits(text):
    return text != "" and all("0" <= ch <= "9" for ch in text)


def _brand_for(digits):
    length = len(digits)
    if digits[:2] in ("34", "37"):
        return "amex" if length == 15 else None
    if digits[0] == "4":
        return "visa" if length in (13, 16, 19) else None
    if 51 <= int(digits[:2]) <= 55 or (length >= 4 and 2221 <= int(digits[:4]) <= 2720):
        return "mastercard" if length == 16 else None
    if digits.startswith("6011") or digits.startswith("65") or (length >= 3 and 644 <= int(digits[:3]) <= 649):
        return "discover" if length in (16, 19) else None
    return None


def card_brand(number):
    """Return the card brand for a Luhn-valid number, or None."""
    if not isinstance(number, str):
        raise TypeError("number must be a str")
    digits = strip_separators(number)
    if not _is_ascii_digits(digits) or len(digits) < 2:
        return None
    if not _luhn_ok(digits):
        return None
    return _brand_for(digits)


def is_valid_iban(iban):
    """Return True if iban is a valid IBAN for a supported country."""
    if not isinstance(iban, str):
        raise TypeError("iban must be a str")
    compact = iban.replace(" ", "").upper()
    if len(compact) < 5:
        return False
    country, check, rest = compact[:2], compact[2:4], compact[4:]
    if not all("A" <= ch <= "Z" for ch in country):
        return False
    if not _is_ascii_digits(check):
        return False
    if not all("A" <= ch <= "Z" or "0" <= ch <= "9" for ch in rest):
        return False
    if IBAN_LENGTHS.get(country) != len(compact):
        return False
    rearranged = rest + country + check
    numeric = "".join(str(ord(ch) - 55) if "A" <= ch <= "Z" else ch for ch in rearranged)
    return int(numeric) % 97 == 1
