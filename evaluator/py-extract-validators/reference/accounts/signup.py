"""New account registration."""

from . import validators
from .errors import ValidationError


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
        "username": validators.validate_username(form["username"]),
        "email": validators.validate_email(form["email"]),
        "phone": None,
    }
    if form.get("phone", "").strip():
        account["phone"] = validators.validate_phone(form["phone"])
    return account
