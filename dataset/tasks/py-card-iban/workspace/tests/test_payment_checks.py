import unittest

from payment_checks import mask_card, strip_separators


class MaskCardTest(unittest.TestCase):
    def test_masks_all_but_last_four(self):
        self.assertEqual(mask_card("4111 1111 1111 1111"), "************1111")

    def test_rejects_short_input(self):
        with self.assertRaises(ValueError):
            mask_card("12-3")

    def test_strip_separators(self):
        self.assertEqual(strip_separators("12 34-56"), "123456")


if __name__ == "__main__":
    unittest.main()
