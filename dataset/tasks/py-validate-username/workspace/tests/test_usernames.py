import unittest

from accounts.usernames import is_reserved, normalize_username


class NormalizeTest(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_username("  Ada.L "), "ada.l")

    def test_reserved(self):
        self.assertTrue(is_reserved("admin"))
        self.assertFalse(is_reserved("ada"))


if __name__ == "__main__":
    unittest.main()
