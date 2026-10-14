import contextlib
import unittest
from unittest import mock

from accounts import profile, signup, validators
from accounts.errors import ValidationError

BASE = {"username": "ada", "email": "ada@example.org", "phone": None, "display_name": "Ada"}


def form(**overrides):
    data = {"username": "Ada_L", "email": "ada@example.org", "password": "correct horse"}
    data.update(overrides)
    return data


@contextlib.contextmanager
def spy(name, *modules):
    """Wrap validators.<name> wherever the given modules can reach it, recording calls."""
    calls = []
    real = getattr(validators, name)

    def wrapper(value, *args, **kwargs):
        calls.append(value)
        return real(value, *args, **kwargs)

    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(validators, name, wrapper))
        for module in modules:
            if getattr(module, name, None) is real:
                stack.enter_context(mock.patch.object(module, name, wrapper))
        yield calls


class ValidatorFunctionsTest(unittest.TestCase):
    def assertRejects(self, func, value, field):
        with self.assertRaises(ValidationError, msg=repr(value)) as ctx:
            func(value)
        self.assertEqual(ctx.exception.field, field)

    def test_email(self):
        self.assertEqual(validators.validate_email("  Ada@Example.ORG "), "ada@example.org")
        for bad in ["ada", "a@b@c.org", "@example.org", "ada@", "ad a@example.org",
                    "ada@example", "ada@.example.org", "ada@example.org.", "ada@example..org"]:
            self.assertRejects(validators.validate_email, bad, "email")

    def test_username(self):
        self.assertEqual(validators.validate_username(" Ada_99 "), "ada_99")
        for bad in ["ab", "a" * 21, "9lives", "_ada", "ada-l", "adé", "Root"]:
            self.assertRejects(validators.validate_username, bad, "username")
        self.assertEqual(validators.validate_username("a" * 20), "a" * 20)

    def test_reserved_names_live_in_validators(self):
        self.assertEqual(validators.RESERVED_USERNAMES, {"admin", "root", "support", "system"})

    def test_phone(self):
        self.assertEqual(validators.validate_phone("+1 (415) 555-0123"), "+14155550123")
        self.assertEqual(validators.validate_phone("555.0100"), "5550100")
        for bad in ["", "+", "555-01x0", "123456", "1" * 16, "(+1) 4155550123", "５５５０１００"]:
            self.assertRejects(validators.validate_phone, bad, "phone")

    def test_display_name(self):
        self.assertEqual(validators.validate_display_name("  Ada \t  Lovelace "), "Ada Lovelace")
        self.assertEqual(validators.validate_display_name("x" * 50), "x" * 50)
        for bad in ["", "   ", "x" * 51, "Ada\x07"]:
            self.assertRejects(validators.validate_display_name, bad, "display_name")


class ModulesUseValidatorsTest(unittest.TestCase):
    def test_signup_calls_shared_validators(self):
        with spy("validate_email", signup) as emails, spy("validate_username", signup) as names, \
                spy("validate_phone", signup) as phones:
            signup.register(form(phone="555 0100"))
        self.assertEqual(emails, ["ada@example.org"])
        self.assertEqual(names, ["Ada_L"])
        self.assertEqual(phones, ["555 0100"])

    def test_profile_calls_shared_validators(self):
        with spy("validate_email", profile) as emails, spy("validate_username", profile) as names, \
                spy("validate_phone", profile) as phones, spy("validate_display_name", profile) as display:
            profile.update_profile(BASE, {"email": "A@B.co", "username": "Bob", "phone": "5550100",
                                          "display_name": "Bob B"})
        self.assertEqual((emails, names, phones, display), (["A@B.co"], ["Bob"], ["5550100"], ["Bob B"]))

    def test_old_private_helpers_removed(self):
        for helper in ("_clean_email", "_clean_username", "_clean_phone"):
            self.assertFalse(hasattr(signup, helper), helper)


class BehaviourUnchangedTest(unittest.TestCase):
    def test_register(self):
        self.assertEqual(
            signup.register(form(username=" Grace_H ", email=" GRACE@Navy.MIL ", phone="+1 202.555.0143")),
            {"username": "grace_h", "email": "grace@navy.mil", "phone": "+12025550143"},
        )

    def test_register_error_fields(self):
        cases = [
            (form(email=""), "email"),
            (form(password="  "), "password"),
            (form(username="ab"), "username"),
            (form(email="grace@navy"), "email"),
            (form(phone="12-34"), "phone"),
            (form(username="support"), "username"),
        ]
        for data, field in cases:
            with self.assertRaises(ValidationError) as ctx:
                signup.register(data)
            self.assertEqual(ctx.exception.field, field)

    def test_update_profile(self):
        updated = profile.update_profile(BASE, {"email": " Ada@Lovelace.Dev ", "username": "Countess_A",
                                                "phone": "", "display_name": " Ada  L "})
        self.assertEqual(updated, {"username": "countess_a", "email": "ada@lovelace.dev", "phone": None,
                                   "display_name": "Ada L"})
        self.assertEqual(BASE["email"], "ada@example.org")

    def test_update_profile_errors(self):
        cases = [
            ({"email": "x@y"}, "email"),
            ({"username": "admin"}, "username"),
            ({"phone": "+"}, "phone"),
            ({"display_name": "\t"}, "display_name"),
            ({"id": 3}, "id"),
        ]
        for changes, field in cases:
            with self.assertRaises(ValidationError) as ctx:
                profile.update_profile(BASE, changes)
            self.assertEqual(ctx.exception.field, field)


if __name__ == "__main__":
    unittest.main()
