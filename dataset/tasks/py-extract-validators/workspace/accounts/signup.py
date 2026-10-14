"""New account registration."""

import re

from .errors import ValidationError

_USERNAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
RESERVED_USERNAMES = {"admin", "root", "support", "system"}


def _clean_email(value):
    email = value.strip().lower()
    if email.count("@") != 1:
        raise ValidationError("email", "must contain exactly one @")
    local, domain = email.split("@")
    if not local or not domain:
        raise ValidationError("email", "missing local part or domain")
    if any(ch.isspace() for ch in email):
        raise ValidationError("email", "must not contain spaces")
    if "." not in domain or domain.startswith(".") or domain.endswith(".") or ".." in domain:
        raise ValidationError("email", "invalid domain")
    return email


def _clean_username(value):
    username = value.strip()
    if not 3 <= len(username) <= 20:
        raise ValidationError("username", "must be 3 to 20 characters")
    if not _USERNAME_RE.fullmatch(username):
        raise ValidationError("username", "letters, digits and _ only, starting with a letter")
    username = username.lower()
    if username in RESERVED_USERNAMES:
        raise ValidationError("username", "is reserved")
    return username


def _clean_phone(value):
    raw = value.strip()
    plus = raw.startswith("+")
    if plus:
        raw = raw[1:]
    for sep in " -.()":
        raw = raw.replace(sep, "")
    if not raw.isdigit() or not raw.isascii():
        raise ValidationError("phone", "digits only")
    if not 7 <= len(raw) <= 15:
        raise ValidationError("phone", "must have 7 to 15 digits")
    return ("+" if plus else "") + raw


def register(form):
    """Validate a sign-up form (a dict of strings) and return the normalised account.

    Required keys: username, email, password. Optional: phone.
    """
    for key in ("username", "email", "password"):
        if not form.get(key, "").strip():
            raise ValidationError(key, "is required")
    if len(form["password"]) < 10:
        raise ValidationError("password", "must be at least 10 characters")
    account = {
        "username": _clean_username(form["username"]),
        "email": _clean_email(form["email"]),
        "phone": None,
    }
    if form.get("phone", "").strip():
        account["phone"] = _clean_phone(form["phone"])
    return account
