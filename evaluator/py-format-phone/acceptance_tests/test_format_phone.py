import unittest

from contacts import format_us_phone


class FormatUsPhoneTest(unittest.TestCase):
    def test_plain_digits(self):
        self.assertEqual(format_us_phone("4155550123"), "(415) 555-0123")

    def test_separators_are_ignored(self):
        self.assertEqual(format_us_phone("415-555-0123"), "(415) 555-0123")
        self.assertEqual(format_us_phone("(415) 555.0123"), "(415) 555-0123")
        self.assertEqual(format_us_phone("  415 555 0123 "), "(415) 555-0123")

    def test_leading_country_code(self):
        self.assertEqual(format_us_phone("+1 415 555 0123"), "(415) 555-0123")
        self.assertEqual(format_us_phone("14155550123"), "(415) 555-0123")

    def test_wrong_length(self):
        for raw in ["415555012", "415555012345", "24155550123", "", "+1"]:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    format_us_phone(raw)

    def test_letters_and_other_characters(self):
        for raw in ["415-555-CALL", "415/555/0123", "415555012x"]:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    format_us_phone(raw)

    def test_area_code_or_exchange_starting_with_0_or_1(self):
        for raw in ["015-555-0123", "115-555-0123", "415-055-0123", "415-155-0123", "1 115 555 0123"]:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    format_us_phone(raw)
