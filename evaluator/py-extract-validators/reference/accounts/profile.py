"""Profile editing."""

from . import validators
from .errors import ValidationError

EDITABLE = ("display_name", "email", "phone", "username")

_VALIDATORS = {
    "display_name": "validate_display_name",
    "email": "validate_email",
    "phone": "validate_phone",
    "username": "validate_username",
}


def update_profile(profile, changes):
    """Return a new profile dict with `changes` applied. Unknown keys raise ValidationError.

    An empty or blank phone clears it (None). Other fields cannot be blank.
    """
    updated = dict(profile)
    for key, value in changes.items():
        if key not in EDITABLE:
            raise ValidationError(key, "cannot be changed")
        if key == "phone" and not value.strip():
            updated["phone"] = None
            continue
        updated[key] = getattr(validators, _VALIDATORS[key])(value)
    return updated
