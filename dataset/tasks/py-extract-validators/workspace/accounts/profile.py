"""Profile editing."""

from .errors import ValidationError

EDITABLE = ("display_name", "email", "phone", "username")
RESERVED_USERNAMES = {"admin", "root", "support", "system"}


def update_profile(profile, changes):
    """Return a new profile dict with `changes` applied. Unknown keys raise ValidationError.

    An empty or blank phone clears it (None). Other fields cannot be blank.
    """
    updated = dict(profile)
    for key, value in changes.items():
        if key not in EDITABLE:
            raise ValidationError(key, "cannot be changed")

        if key == "display_name":
            name = " ".join(value.split())
            if not name:
                raise ValidationError("display_name", "is required")
            if len(name) > 50:
                raise ValidationError("display_name", "must be at most 50 characters")
            if any(not ch.isprintable() for ch in name):
                raise ValidationError("display_name", "contains control characters")
            updated["display_name"] = name

        elif key == "email":
            email = value.strip().lower()
            if email.count("@") != 1:
                raise ValidationError("email", "must contain exactly one @")
            local, _, domain = email.partition("@")
            if local == "" or domain == "":
                raise ValidationError("email", "missing local part or domain")
            if any(ch.isspace() for ch in email):
                raise ValidationError("email", "must not contain spaces")
            parts = domain.split(".")
            if len(parts) < 2 or any(part == "" for part in parts):
                raise ValidationError("email", "invalid domain")
            updated["email"] = email

        elif key == "phone":
            if not value.strip():
                updated["phone"] = None
                continue
            digits = value.strip()
            prefix = ""
            if digits[0] == "+":
                prefix, digits = "+", digits[1:]
            digits = "".join(ch for ch in digits if ch not in " -.()")
            if not (digits.isascii() and digits.isdigit()):
                raise ValidationError("phone", "digits only")
            if len(digits) < 7 or len(digits) > 15:
                raise ValidationError("phone", "must have 7 to 15 digits")
            updated["phone"] = prefix + digits

        elif key == "username":
            username = value.strip()
            if len(username) < 3 or len(username) > 20:
                raise ValidationError("username", "must be 3 to 20 characters")
            if not (username[0].isascii() and username[0].isalpha()) or not all(
                ch.isascii() and (ch.isalnum() or ch == "_") for ch in username
            ):
                raise ValidationError("username", "letters, digits and _ only, starting with a letter")
            if username.lower() in RESERVED_USERNAMES:
                raise ValidationError("username", "is reserved")
            updated["username"] = username.lower()
    return updated
