import unittest

from calc.functions import CONSTANTS, FUNCTIONS, arity_ok


class FunctionTableTest(unittest.TestCase):
    def test_arity(self):
        self.assertTrue(arity_ok("min", 5))
        self.assertFalse(arity_ok("min", 0))
        self.assertFalse(arity_ok("hypot", 1))

    def test_tables(self):
        self.assertIn("sqrt", FUNCTIONS)
        self.assertIn("pi", CONSTANTS)


if __name__ == "__main__":
    unittest.main()
