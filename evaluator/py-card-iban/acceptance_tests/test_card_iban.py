import unittest

from payment_checks import card_brand, is_valid_iban, mask_card


class CardBrandTest(unittest.TestCase):
    def test_visa_lengths(self):
        self.assertEqual(card_brand("4111111111111111"), "visa")
        self.assertEqual(card_brand("4222222222222"), "visa")
        self.assertEqual(card_brand("4111111111111111110"), "visa")

    def test_visa_wrong_length(self):
        self.assertIsNone(card_brand("41111111111114"))

    def test_amex(self):
        self.assertEqual(card_brand("378282246310005"), "amex")
        self.assertEqual(card_brand("340000000000009"), "amex")
        self.assertIsNone(card_brand("370000000000000007"))

    def test_mastercard(self):
        self.assertEqual(card_brand("5555555555554444"), "mastercard")
        self.assertEqual(card_brand("2223003122003222"), "mastercard")

    def test_mastercard_two_series_boundaries(self):
        self.assertEqual(card_brand("2221000000000009"), "mastercard")
        self.assertEqual(card_brand("2720000000000005"), "mastercard")
        self.assertIsNone(card_brand("2220000000000000"))
        self.assertIsNone(card_brand("2721000000000004"))

    def test_mastercard_other_prefixes(self):
        self.assertIsNone(card_brand("5600000000000003"))

    def test_discover(self):
        self.assertEqual(card_brand("6011111111111117"), "discover")
        self.assertEqual(card_brand("6500000000000002"), "discover")
        self.assertEqual(card_brand("6445644564456445"), "discover")
        self.assertEqual(card_brand("6011000000000000001"), "discover")
        self.assertIsNone(card_brand("6430000000000007"))
        self.assertIsNone(card_brand("64400000000000002"))

    def test_unknown_prefix(self):
        self.assertIsNone(card_brand("3530111333300000"))

    def test_luhn_failure(self):
        self.assertIsNone(card_brand("4111111111111112"))
        self.assertIsNone(card_brand("5555555555554445"))

    def test_separators(self):
        self.assertEqual(card_brand("4111 1111 1111 1111"), "visa")
        self.assertEqual(card_brand("4111-1111-1111-1111"), "visa")
        self.assertEqual(card_brand(" 3782 822463 10005 "), "amex")

    def test_other_characters(self):
        self.assertIsNone(card_brand("4111.1111.1111.1111"))
        self.assertIsNone(card_brand("4111a11111111111"))
        self.assertIsNone(card_brand(""))
        self.assertIsNone(card_brand("   "))

    def test_type_error(self):
        with self.assertRaises(TypeError):
            card_brand(4111111111111111)
        with self.assertRaises(TypeError):
            card_brand(None)


class IbanTest(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(is_valid_iban("GB82 WEST 1234 5698 7654 32"))
        self.assertTrue(is_valid_iban("DE89370400440532013000"))
        self.assertTrue(is_valid_iban("NL91ABNA0417164300"))
        self.assertTrue(is_valid_iban("FR1420041010050500013M02606"))
        self.assertTrue(is_valid_iban("NO9386011117947"))

    def test_lowercase_and_spaces(self):
        self.assertTrue(is_valid_iban("gb82west12345698765432"))
        self.assertTrue(is_valid_iban("  de89 3704 0044 0532 0130 00 "))

    def test_bad_checksum(self):
        self.assertFalse(is_valid_iban("GB82 WEST 1234 5698 7654 33"))
        self.assertFalse(is_valid_iban("GB28 WEST 1234 5698 7654 32"))

    def test_wrong_length(self):
        self.assertFalse(is_valid_iban("DE893704004405320130000"))
        self.assertFalse(is_valid_iban("DE8937040044053201300"))

    def test_unknown_country(self):
        # Valid mod-97 checksum but the country is not in the table.
        self.assertFalse(is_valid_iban("US64SVBKUS6S3300958879"))

    def test_other_separators(self):
        self.assertFalse(is_valid_iban("GB82-WEST-1234-5698-7654-32"))
        self.assertFalse(is_valid_iban("GB82.WEST.1234.5698.7654.32"))

    def test_structure(self):
        self.assertFalse(is_valid_iban("GBXX WEST 1234 5698 7654 32"))
        self.assertFalse(is_valid_iban("1282 WEST 1234 5698 7654 32"))
        self.assertFalse(is_valid_iban(""))

    def test_type_error(self):
        with self.assertRaises(TypeError):
            is_valid_iban(None)


class ExistingHelpersTest(unittest.TestCase):
    def test_mask_card_still_works(self):
        self.assertEqual(mask_card("5555-5555-5555-4444"), "************4444")


if __name__ == "__main__":
    unittest.main()
