import unittest

from accounts.usernames import is_valid_username


class IsValidUsernameTest(unittest.TestCase):
    def test_valid_names(self):
        self.assertTrue(is_valid_username("ada"))
        self.assertTrue(is_valid_username("ada.lovelace_1815"))
        self.assertTrue(is_valid_username("a-b.c_d"))
        self.assertTrue(is_valid_username("x99"))

    def test_length_bounds(self):
        self.assertFalse(is_valid_username("ab"))
        self.assertTrue(is_valid_username("abc"))
        self.assertTrue(is_valid_username("a" * 20))
        self.assertFalse(is_valid_username("a" * 21))
        self.assertFalse(is_valid_username(""))

    def test_first_character_must_be_letter(self):
        self.assertFalse(is_valid_username("1ada"))
        self.assertFalse(is_valid_username("_ada"))
        self.assertFalse(is_valid_username(".ada"))

    def test_disallowed_characters(self):
        self.assertFalse(is_valid_username("Ada"))
        self.assertFalse(is_valid_username("ada lovelace"))
        self.assertFalse(is_valid_username("ada@home"))
        self.assertFalse(is_valid_username("adé"))
        self.assertFalse(is_valid_username("ada\n"))

    def test_doubled_separators(self):
        self.assertFalse(is_valid_username("ada..l"))
        self.assertFalse(is_valid_username("ada__l"))
        self.assertFalse(is_valid_username("ada._l"))
        self.assertFalse(is_valid_username("ada-.l"))

    def test_trailing_separator(self):
        self.assertFalse(is_valid_username("ada."))
        self.assertFalse(is_valid_username("ada_"))
        self.assertFalse(is_valid_username("ada-"))

    def test_non_strings(self):
        self.assertFalse(is_valid_username(None))
        self.assertFalse(is_valid_username(12345))
