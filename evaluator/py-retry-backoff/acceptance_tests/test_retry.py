import unittest

from errors import PermanentError, TransientError
from httpclient import fetch_json
from retry import retry, retrying


class Flaky:
    """Fails with the given exceptions in order, then returns 'done'."""

    def __init__(self, *failures):
        self.failures = list(failures)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.failures:
            raise self.failures.pop(0)
        return "done"


class Recorder:
    def __init__(self):
        self.delays = []

    def __call__(self, seconds):
        self.delays.append(seconds)


class RetryTest(unittest.TestCase):
    def test_success_first_try_does_not_sleep(self):
        sleep = Recorder()
        self.assertEqual(retry(lambda: 42, sleep=sleep), 42)
        self.assertEqual(sleep.delays, [])

    def test_exponential_delays(self):
        fn = Flaky(ValueError(), ValueError(), ValueError())
        sleep = Recorder()
        self.assertEqual(retry(fn, attempts=4, base_delay=0.5, max_delay=10, sleep=sleep), "done")
        self.assertEqual(fn.calls, 4)
        self.assertEqual(sleep.delays, [0.5, 1.0, 2.0])

    def test_delay_is_capped(self):
        fn = Flaky(*[OSError() for _ in range(5)])
        sleep = Recorder()
        retry(fn, attempts=6, base_delay=1, max_delay=3, sleep=sleep)
        self.assertEqual(sleep.delays, [1, 2, 3, 3, 3])

    def test_reraises_last_error_without_final_sleep(self):
        first, second, last = KeyError("a"), KeyError("b"), KeyError("c")
        fn = Flaky(first, second, last)
        sleep = Recorder()
        with self.assertRaises(KeyError) as ctx:
            retry(fn, attempts=3, base_delay=0.1, sleep=sleep)
        self.assertIs(ctx.exception, last)
        self.assertEqual(fn.calls, 3)
        self.assertEqual(len(sleep.delays), 2)

    def test_non_matching_exception_is_not_retried(self):
        fn = Flaky(PermanentError("nope"))
        sleep = Recorder()
        with self.assertRaises(PermanentError):
            retry(fn, attempts=5, retry_on=TransientError, sleep=sleep)
        self.assertEqual(fn.calls, 1)
        self.assertEqual(sleep.delays, [])

    def test_retry_on_accepts_a_tuple(self):
        fn = Flaky(TransientError(), KeyError())
        self.assertEqual(retry(fn, attempts=3, retry_on=(TransientError, KeyError), sleep=Recorder()), "done")

    def test_single_attempt(self):
        fn = Flaky(ValueError())
        sleep = Recorder()
        with self.assertRaises(ValueError):
            retry(fn, attempts=1, sleep=sleep)
        self.assertEqual(sleep.delays, [])

    def test_invalid_arguments(self):
        fn = Flaky()
        with self.assertRaises(ValueError):
            retry(fn, attempts=0, sleep=Recorder())
        with self.assertRaises(ValueError):
            retry(fn, base_delay=-1, sleep=Recorder())
        with self.assertRaises(ValueError):
            retry(fn, max_delay=-1, sleep=Recorder())
        self.assertEqual(fn.calls, 0)

    def test_on_retry_callback(self):
        e1, e2 = ValueError(1), ValueError(2)
        fn = Flaky(e1, e2)
        seen = []
        retry(fn, attempts=3, base_delay=0.25, sleep=Recorder(),
              on_retry=lambda attempt, exc, delay: seen.append((attempt, exc, delay)))
        self.assertEqual(seen, [(1, e1, 0.25), (2, e2, 0.5)])

    def test_on_retry_not_called_after_final_failure(self):
        seen = []
        with self.assertRaises(ValueError):
            retry(Flaky(ValueError(), ValueError()), attempts=2, sleep=Recorder(),
                  on_retry=lambda *a: seen.append(a))
        self.assertEqual(len(seen), 1)


class RetryingDecoratorTest(unittest.TestCase):
    def test_passes_arguments_and_retries(self):
        calls = []
        sleep = Recorder()

        @retrying(attempts=3, base_delay=1, sleep=sleep)
        def add(a, b=0):
            """Add things."""
            calls.append((a, b))
            if len(calls) < 2:
                raise ConnectionError()
            return a + b

        self.assertEqual(add(2, b=3), 5)
        self.assertEqual(calls, [(2, 3), (2, 3)])
        self.assertEqual(sleep.delays, [1])
        self.assertEqual(add.__name__, "add")
        self.assertEqual(add.__doc__, "Add things.")


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def get(self, url):
        self.calls += 1
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FetchJsonTest(unittest.TestCase):
    def test_fetch_json_uses_backoff(self):
        transport = FakeTransport([TransientError(), TransientError(), TransientError(), '{"n": 1}'])
        sleep = Recorder()
        self.assertEqual(fetch_json(transport, "u", sleep=sleep), {"n": 1})
        self.assertEqual(sleep.delays, [0.5, 1.0, 2.0])

    def test_fetch_json_gives_up_after_four_calls(self):
        failures = [TransientError(str(i)) for i in range(5)]
        transport = FakeTransport(failures)
        sleep = Recorder()
        with self.assertRaises(TransientError) as ctx:
            fetch_json(transport, "u", sleep=sleep)
        self.assertIs(ctx.exception, failures[3])
        self.assertEqual(transport.calls, 4)
        self.assertEqual(sleep.delays, [0.5, 1.0, 2.0])

    def test_fetch_json_does_not_retry_permanent_errors(self):
        transport = FakeTransport([PermanentError("400")])
        sleep = Recorder()
        with self.assertRaises(PermanentError):
            fetch_json(transport, "u", sleep=sleep)
        self.assertEqual(transport.calls, 1)
        self.assertEqual(sleep.delays, [])
