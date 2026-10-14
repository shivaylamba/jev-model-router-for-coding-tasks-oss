import unittest

from accounts.errors import ValidationError
from accounts.signup import register


def form(**overrides):
    data = {"username": "Ada_L", "email": " Ada@Example.org ", "password": "correct horse"}
    data.update(overrides)
    return data


class RegisterTest(unittest.TestCase):
    def test_normalises(self):
        self.assertEqual(
            register(form(phone="+44 (20) 7946-0018")),
            {"username": "ada_l", "email": "ada@example.org", "phone": "+442079460018"},
        )

    def test_phone_optional(self):
        self.assertIsNone(register(form())["phone"])

    def test_bad_email(self):
        with self.assertRaises(ValidationError) as ctx:
            register(form(email="ada@example"))
        self.assertEqual(ctx.exception.field, "email")

    def test_reserved_username(self):
        with self.assertRaises(ValidationError) as ctx:
            register(form(username="Admin"))
        self.assertEqual(ctx.exception.field, "username")

    def test_short_password(self):
        with self.assertRaises(ValidationError) as ctx:
            register(form(password="short"))
        self.assertEqual(ctx.exception.field, "password")


if __name__ == "__main__":
    unittest.main()
