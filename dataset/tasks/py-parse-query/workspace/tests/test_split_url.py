import unittest

from urlbits import split_url


class SplitUrlTest(unittest.TestCase):
    def test_all_parts(self):
        self.assertEqual(split_url("https://x.test/a?b=1#top"), ("https://x.test/a", "b=1", "top"))

    def test_no_query(self):
        self.assertEqual(split_url("https://x.test/a#top"), ("https://x.test/a", "", "top"))


if __name__ == "__main__":
    unittest.main()
