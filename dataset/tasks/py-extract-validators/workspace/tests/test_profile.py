import unittest

from accounts.errors import ValidationError
from accounts.profile import update_profile

BASE = {"username": "ada", "email": "ada@example.org", "phone": None, "display_name": "Ada"}


class UpdateProfileTest(unittest.TestCase):
    def test_updates(self):
        updated = update_profile(BASE, {"display_name": "  Ada   Lovelace ", "phone": "555-0100 123"})
        self.assertEqual(updated["display_name"], "Ada Lovelace")
        self.assertEqual(updated["phone"], "5550100123")
        self.assertEqual(BASE["display_name"], "Ada")

    def test_blank_phone_clears(self):
        self.assertIsNone(update_profile({**BASE, "phone": "5550100"}, {"phone": "  "})["phone"])

    def test_unknown_field(self):
        with self.assertRaises(ValidationError) as ctx:
            update_profile(BASE, {"password": "x"})
        self.assertEqual(ctx.exception.field, "password")

    def test_bad_username(self):
        with self.assertRaises(ValidationError) as ctx:
            update_profile(BASE, {"username": "9lives"})
        self.assertEqual(ctx.exception.field, "username")


if __name__ == "__main__":
    unittest.main()
