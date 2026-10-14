import asyncio
import unittest

from ratelimit import RateLimiter
from tests.fake_time import FakeTime, settle


class RateLimiterTest(unittest.IsolatedAsyncioTestCase):
    async def test_waits_for_token(self):
        time = FakeTime()
        limiter = RateLimiter(2.0, 1, 5, clock=time.clock, sleep=time.sleep)
        await limiter.acquire("a")
        task = asyncio.ensure_future(limiter.acquire("a"))
        await settle()
        self.assertFalse(task.done())
        await time.advance(0.5)
        self.assertTrue(task.done())
        self.assertEqual(limiter.in_use, 2)

    async def test_release_hands_slot_over(self):
        time = FakeTime()
        limiter = RateLimiter(1.0, 3, 1, clock=time.clock, sleep=time.sleep)
        await limiter.acquire("a")
        task = asyncio.ensure_future(limiter.acquire("b"))
        await settle()
        limiter.release()
        self.assertEqual(limiter.in_use, 1)
        await settle()
        self.assertTrue(task.done())

    async def test_cancelled_waiter_consumes_nothing(self):
        time = FakeTime()
        limiter = RateLimiter(1.0, 2, 1, clock=time.clock, sleep=time.sleep)
        await limiter.acquire("a")
        task = asyncio.ensure_future(limiter.acquire("b"))
        await settle()
        task.cancel()
        await settle()
        self.assertEqual(limiter.waiting(), 0)
        self.assertEqual(limiter.tokens("b"), 2.0)


if __name__ == "__main__":
    unittest.main()
