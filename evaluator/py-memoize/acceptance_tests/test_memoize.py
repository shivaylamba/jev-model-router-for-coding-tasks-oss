import unittest

from funcutil import CacheInfo, memoize


def counted():
    calls = []

    @memoize
    def add(a, b=0):
        """Add two numbers."""
        calls.append((a, b))
        return a + b

    return add, calls


class MemoizeTest(unittest.TestCase):
    def test_caches_by_arguments(self):
        add, calls = counted()
        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(2, 1), 3)
        self.assertEqual(calls, [(1, 2), (2, 1)])

    def test_cache_info(self):
        add, _ = counted()
        self.assertEqual(add.cache_info(), CacheInfo(hits=0, misses=0, size=0))
        add(1, 2)
        add(1, 2)
        add(3)
        info = add.cache_info()
        self.assertEqual(info, (1, 2, 2))
        self.assertEqual((info.hits, info.misses, info.size), (1, 2, 2))

    def test_keyword_order_does_not_matter(self):
        calls = []

        @memoize
        def f(*, a, b):
            calls.append((a, b))
            return a * b

        self.assertEqual(f(a=2, b=3), 6)
        self.assertEqual(f(b=3, a=2), 6)
        self.assertEqual(len(calls), 1)

    def test_positional_and_keyword_are_separate_entries(self):
        add, calls = counted()
        add(1, 2)
        add(1, b=2)
        self.assertEqual(len(calls), 2)
        self.assertEqual(add.cache_info().size, 2)

    def test_none_is_cached(self):
        calls = []

        @memoize
        def lookup(key):
            calls.append(key)
            return None

        self.assertIsNone(lookup("x"))
        self.assertIsNone(lookup("x"))
        self.assertEqual(calls, ["x"])

    def test_exceptions_are_not_cached(self):
        calls = []

        @memoize
        def flaky(x):
            calls.append(x)
            if len(calls) == 1:
                raise RuntimeError("first call fails")
            return x

        with self.assertRaises(RuntimeError):
            flaky(1)
        self.assertEqual(flaky(1), 1)
        self.assertEqual(len(calls), 2)
        self.assertEqual(flaky.cache_info(), (0, 2, 1))

    def test_cache_clear_resets_everything(self):
        add, calls = counted()
        add(1, 2)
        add(1, 2)
        add.cache_clear()
        self.assertEqual(add.cache_info(), (0, 0, 0))
        add(1, 2)
        self.assertEqual(len(calls), 2)

    def test_unhashable_arguments(self):
        add, calls = counted()
        with self.assertRaises(TypeError):
            add([1], [2])
        self.assertEqual(calls, [])

    def test_separate_functions_have_separate_caches(self):
        add, _ = counted()
        other, _ = counted()
        add(1)
        self.assertEqual(other.cache_info().misses, 0)

    def test_wraps_metadata(self):
        add, _ = counted()
        self.assertEqual(add.__name__, "add")
        self.assertEqual(add.__doc__, "Add two numbers.")


if __name__ == "__main__":
    unittest.main()
