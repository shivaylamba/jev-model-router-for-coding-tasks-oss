import asyncio
import unittest

from ratelimit import RateLimiter


async def settle(rounds=50):
    for _ in range(rounds):
        await asyncio.sleep(0)


class FakeTime:
    def __init__(self):
        self.now = 0.0
        self.sleep_calls = []
        self._sleepers = []

    def clock(self):
        return self.now

    async def sleep(self, delay):
        self.sleep_calls.append(delay)
        if delay <= 0:
            await asyncio.sleep(0)
            return
        entry = (self.now + delay, asyncio.get_running_loop().create_future())
        self._sleepers.append(entry)
        try:
            await entry[1]
        finally:
            if entry in self._sleepers:
                self._sleepers.remove(entry)

    async def advance(self, seconds):
        self.now += seconds
        for _ in range(20):
            for entry in [entry for entry in self._sleepers if entry[0] <= self.now]:
                self._sleepers.remove(entry)
                if not entry[1].done():
                    entry[1].set_result(None)
            await settle()
            if not any(entry[0] <= self.now for entry in self._sleepers):
                return


class LimiterTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tasks = []
        self.order = []

    def make(self, rate=1.0, burst=1, max_concurrent=10):
        self.time = FakeTime()
        self.order = []
        self.tasks = []
        return RateLimiter(rate, burst, max_concurrent, clock=self.time.clock, sleep=self.time.sleep)

    def start(self, limiter, key, label=None):
        async def run():
            await limiter.acquire(key)
            self.order.append(label or key)

        task = asyncio.ensure_future(run())
        self.tasks.append(task)
        return task

    async def asyncTearDown(self):
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)


class ConstructionTest(LimiterTestCase):
    async def test_invalid_arguments(self):
        time = FakeTime()
        with self.assertRaises(ValueError):
            RateLimiter(0, 1, 1, clock=time.clock, sleep=time.sleep)
        with self.assertRaises(ValueError):
            RateLimiter(1, 0, 1, clock=time.clock, sleep=time.sleep)
        with self.assertRaises(ValueError):
            RateLimiter(1, 1, 0, clock=time.clock, sleep=time.sleep)

    async def test_fresh_state(self):
        limiter = self.make(burst=4)
        self.assertEqual(limiter.in_use, 0)
        self.assertEqual(limiter.tokens("never-used"), 4.0)
        self.assertEqual(limiter.waiting(), 0)

    async def test_release_without_slot(self):
        limiter = self.make()
        with self.assertRaises(RuntimeError):
            limiter.release()


class TokenTest(LimiterTestCase):
    async def test_immediate_acquire_does_not_sleep(self):
        limiter = self.make(burst=2)
        await limiter.acquire("a")
        await limiter.acquire("a")
        self.assertEqual(limiter.in_use, 2)
        self.assertEqual(limiter.tokens("a"), 0.0)
        self.assertEqual(self.time.sleep_calls, [])

    async def test_waits_for_refill_with_exact_sleep(self):
        limiter = self.make(rate=2.0, burst=1)
        await limiter.acquire("a")
        limiter.release()
        task = self.start(limiter, "a")
        await settle()
        self.assertFalse(task.done())
        self.assertEqual(limiter.waiting("a"), 1)
        self.assertEqual(set(self.time.sleep_calls), {0.5})
        await self.time.advance(0.25)
        self.assertFalse(task.done())
        await self.time.advance(0.25)
        self.assertTrue(task.done())
        self.assertEqual(limiter.waiting("a"), 0)

    async def test_bucket_capped_at_burst(self):
        limiter = self.make(rate=1.0, burst=3)
        for _ in range(3):
            await limiter.acquire("a")
        await self.time.advance(10)
        self.assertEqual(limiter.tokens("a"), 3.0)

    async def test_fifo_per_key(self):
        limiter = self.make(rate=1.0, burst=1)
        await limiter.acquire("a")
        for label in ("a1", "a2", "a3"):
            self.start(limiter, "a", label)
        await settle()
        self.assertEqual(limiter.waiting("a"), 3)
        await self.time.advance(1)
        self.assertEqual(self.order, ["a1"])
        await self.time.advance(1)
        self.assertEqual(self.order, ["a1", "a2"])
        await self.time.advance(1)
        self.assertEqual(self.order, ["a1", "a2", "a3"])

    async def test_other_keys_not_held_up(self):
        limiter = self.make(rate=1.0, burst=1)
        await limiter.acquire("a")
        waiter = self.start(limiter, "a")
        await settle()
        await limiter.acquire("b")
        self.assertFalse(waiter.done())
        self.assertEqual(limiter.in_use, 2)


class ConcurrencyTest(LimiterTestCase):
    async def test_cap_and_release_hands_over(self):
        limiter = self.make(burst=5, max_concurrent=2)
        await limiter.acquire("a")
        await limiter.acquire("a")
        task = self.start(limiter, "b")
        await settle()
        self.assertFalse(task.done())
        self.assertEqual(limiter.waiting(), 1)
        self.assertEqual(self.time.sleep_calls, [])
        limiter.release()
        self.assertEqual(limiter.in_use, 2)
        self.assertEqual(limiter.waiting(), 0)
        await settle()
        self.assertTrue(task.done())

    async def test_slot_goes_to_earliest_caller_across_keys(self):
        limiter = self.make(burst=5, max_concurrent=1)
        await limiter.acquire("x")
        self.start(limiter, "c")
        await settle()
        self.start(limiter, "d")
        await settle()
        limiter.release()
        await settle()
        self.start(limiter, "e")
        await settle()
        limiter.release()
        await settle()
        limiter.release()
        await settle()
        self.assertEqual(self.order, ["c", "d", "e"])

    async def test_key_without_token_does_not_block_slot(self):
        limiter = self.make(rate=1.0, burst=1, max_concurrent=1)
        await limiter.acquire("a")
        limiter.release()
        await limiter.acquire("b")
        self.start(limiter, "a")
        await settle()
        self.start(limiter, "c")
        await settle()
        limiter.release()
        await settle()
        self.assertEqual(self.order, ["c"])
        await self.time.advance(1)
        self.assertEqual(self.order, ["c"])
        limiter.release()
        await settle()
        self.assertEqual(self.order, ["c", "a"])

    async def test_limit_context_manager_releases_on_error(self):
        limiter = self.make(burst=2, max_concurrent=1)
        with self.assertRaises(KeyError):
            async with limiter.limit("a"):
                self.assertEqual(limiter.in_use, 1)
                raise KeyError("boom")
        self.assertEqual(limiter.in_use, 0)
        async with limiter.limit("a"):
            pass
        self.assertEqual(limiter.in_use, 0)


class CancellationTest(LimiterTestCase):
    async def test_cancel_head_waiting_for_token(self):
        limiter = self.make(rate=1.0, burst=1)
        await limiter.acquire("a")
        first = self.start(limiter, "a", "first")
        second = self.start(limiter, "a", "second")
        await settle()
        first.cancel()
        await settle()
        self.assertTrue(first.cancelled())
        self.assertEqual(limiter.waiting("a"), 1)
        await self.time.advance(1)
        self.assertTrue(second.done())
        self.assertEqual(self.order, ["second"])
        self.assertEqual(limiter.tokens("a"), 0.0)
        self.assertEqual(limiter.in_use, 2)

    async def test_cancel_while_waiting_for_slot(self):
        limiter = self.make(burst=2, max_concurrent=1)
        await limiter.acquire("x")
        task = self.start(limiter, "b")
        await settle()
        task.cancel()
        await settle()
        self.assertTrue(task.cancelled())
        self.assertEqual(limiter.waiting(), 0)
        limiter.release()
        self.assertEqual(limiter.in_use, 0)
        self.assertEqual(limiter.tokens("b"), 2.0)

    async def test_cancel_after_grant_is_undone(self):
        limiter = self.make(burst=1, max_concurrent=1)
        await limiter.acquire("x")
        first = self.start(limiter, "b")
        second = self.start(limiter, "c")
        await settle()
        limiter.release()
        self.assertEqual(limiter.in_use, 1)
        first.cancel()
        await settle()
        self.assertTrue(first.cancelled())
        self.assertEqual(limiter.tokens("b"), 1.0)
        self.assertTrue(second.done())
        self.assertEqual(self.order, ["c"])
        self.assertEqual(limiter.in_use, 1)

    async def test_refunded_token_goes_to_next_request_of_same_key(self):
        limiter = self.make(rate=1.0, burst=1, max_concurrent=1)
        await limiter.acquire("x")
        first = self.start(limiter, "a", "first")
        second = self.start(limiter, "a", "second")
        await settle()
        limiter.release()
        first.cancel()
        await settle()
        self.assertTrue(first.cancelled())
        self.assertEqual(self.order, ["second"])
        self.assertEqual(limiter.tokens("a"), 0.0)
        self.assertEqual(self.time.now, 0.0)
