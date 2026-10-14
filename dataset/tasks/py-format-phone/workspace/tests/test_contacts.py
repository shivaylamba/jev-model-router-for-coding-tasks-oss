import unittest

from contacts import format_name, normalize_email


class ContactsTest(unittest.TestCase):
    def test_format_name(self):
        self.assertEqual(format_name("ada", "LOVELACE"), "Ada Lovelace")
        self.assertEqual(format_name(" grace ", ""), "Grace")

    def test_normalize_email(self):
        self.assertEqual(normalize_email("  Ada@Example.COM "), "ada@example.com")


if __name__ == "__main__":
    unittest.main()
