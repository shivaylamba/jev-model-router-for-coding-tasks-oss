"""Field validators shared by sign-up and profile editing.

Each function takes the raw string, returns the normalised value and raises
ValidationError (with `field` set to the field's name) when it is invalid.
"""

import re

from .errors import ValidationError

RESERVED_USERNAMES = {"admin", "root", "support", "system"}

_USERNAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
_PHONE_SEPARATORS = " -.()"


def validate_email(value):
    email = value.strip().lower()
    if email.count("@") != 1:
        raise ValidationError("email", "must contain exactly one @")
    local, domain = email.split("@")
    if not local or not domain:
        raise ValidationError("email", "missing local part or domain")
    if any(ch.isspace() for ch in email):
        raise ValidationError("email", "must not contain spaces")
    if any(part == "" for part in domain.split(".")) or "." not in domain:
        raise ValidationError("email", "invalid domain")
    return email


def validate_username(value):
    username = value.strip()
    if not 3 <= len(username) <= 20:
        raise ValidationError("username", "must be 3 to 20 characters")
    if not _USERNAME_RE.fullmatch(username):
        raise ValidationError("username", "letters, digits and _ only, starting with a letter")
    username = username.lower()
    if username in RESERVED_USERNAMES:
        raise ValidationError("username", "is reserved")
    return username


def validate_phone(value):
    raw = value.strip()
    prefix = ""
    if raw.startswith("+"):
        prefix, raw = "+", raw[1:]
    raw = "".join(ch for ch in raw if ch not in _PHONE_SEPARATORS)
    if not (raw.isascii() and raw.isdigit()):
        raise ValidationError("phone", "digits only")
    if not 7 <= len(raw) <= 15:
        raise ValidationError("phone", "must have 7 to 15 digits")
    return prefix + raw


def validate_display_name(value):
    name = " ".join(value.split())
    if not name:
        raise ValidationError("display_name", "is required")
    if len(name) > 50:
        raise ValidationError("display_name", "must be at most 50 characters")
    if any(not ch.isprintable() for ch in name):
        raise ValidationError("display_name", "contains control characters")
    return name
