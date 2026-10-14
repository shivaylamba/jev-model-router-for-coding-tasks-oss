import unittest

from ratelimit import TokenBucket


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class TokenBucketTest(unittest.TestCase):
    def test_starts_full_and_refills(self):
        clock = Clock()
        bucket = TokenBucket(rate=2, burst=2, clock=clock)
        self.assertTrue(bucket.try_take())
        self.assertTrue(bucket.try_take())
        self.assertFalse(bucket.try_take())
        self.assertEqual(bucket.time_until_available(), 0.5)
        clock.now = 0.5
        self.assertTrue(bucket.try_take())

    def test_capped_at_burst(self):
        clock = Clock()
        bucket = TokenBucket(rate=1, burst=3, clock=clock)
        clock.now = 100
        self.assertEqual(bucket.available(), 3.0)


if __name__ == "__main__":
    unittest.main()
