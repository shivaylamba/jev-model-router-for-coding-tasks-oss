import unittest

from funcutil import once


class OnceTest(unittest.TestCase):
    def test_runs_once(self):
        calls = []

        @once
        def setup(x):
            calls.append(x)
            return x * 2

        self.assertEqual(setup(1), 2)
        self.assertEqual(setup(5), 2)
        self.assertEqual(calls, [1])


if __name__ == "__main__":
    unittest.main()
