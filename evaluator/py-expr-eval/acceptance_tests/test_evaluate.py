import math
import unittest

from calc import ExprError, evaluate


def error_position(expr, variables=None):
    """Position of the ExprError raised for expr, or None if nothing is raised."""
    try:
        evaluate(expr, variables)
    except ExprError as exc:
        return exc.position
    return None


class ArithmeticTest(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(evaluate("42"), 42.0)
        self.assertIsInstance(evaluate("42"), float)
        self.assertAlmostEqual(evaluate(".5 + 2.25"), 2.75)
        self.assertAlmostEqual(evaluate("1e3 + 2.5E-2"), 1000.025)

    def test_precedence_and_associativity(self):
        self.assertEqual(evaluate("1 + 2 * 3"), 7.0)
        self.assertEqual(evaluate("(1 + 2) * 3"), 9.0)
        self.assertEqual(evaluate("10 - 4 - 3"), 3.0)
        self.assertEqual(evaluate("64 / 4 / 2"), 8.0)
        self.assertEqual(evaluate("2 * 3 % 4"), 2.0)

    def test_power_right_associative(self):
        self.assertEqual(evaluate("2^3^2"), 512.0)
        self.assertEqual(evaluate("2 * 3 ^ 2"), 18.0)

    def test_unary_minus_below_power(self):
        self.assertEqual(evaluate("-2^2"), -4.0)
        self.assertEqual(evaluate("(-2)^2"), 4.0)
        self.assertEqual(evaluate("2^-1"), 0.5)
        self.assertEqual(evaluate("-2^-2"), -0.25)
        self.assertEqual(evaluate("--2"), 2.0)
        self.assertEqual(evaluate("3 - -+2"), 5.0)
        self.assertEqual(evaluate("-3 * 2"), -6.0)

    def test_floored_modulo(self):
        self.assertEqual(evaluate("-7 % 3"), 2.0)
        self.assertEqual(evaluate("7 % -3"), -2.0)

    def test_whitespace(self):
        self.assertEqual(evaluate(" \t1+\t2 "), 3.0)


class NamesAndFunctionsTest(unittest.TestCase):
    def test_variables(self):
        self.assertAlmostEqual(evaluate("base * (1 + rate) ^ years", {"base": 100, "rate": 0.5, "years": 2}), 225.0)
        self.assertEqual(evaluate("_x1 + 1", {"_x1": 2}), 3.0)

    def test_constants_and_override(self):
        self.assertAlmostEqual(evaluate("2 * pi"), 2 * math.pi)
        self.assertAlmostEqual(evaluate("e"), math.e)
        self.assertEqual(evaluate("pi", {"pi": 3}), 3.0)

    def test_functions(self):
        self.assertEqual(evaluate("sqrt(16) + abs(-2)"), 6.0)
        self.assertEqual(evaluate("max(1, 7, 3) - min (4, 2)"), 5.0)
        self.assertEqual(evaluate("hypot(3, 4) ^ 2"), 25.0)
        self.assertEqual(evaluate("max(1 + 1, 2 * 3)"), 6.0)


class SyntaxErrorPositionTest(unittest.TestCase):
    def test_is_value_error(self):
        self.assertTrue(issubclass(ExprError, ValueError))

    def test_end_of_input(self):
        self.assertEqual(error_position(""), 0)
        self.assertEqual(error_position("   "), 3)
        self.assertEqual(error_position("1 +"), 3)
        self.assertEqual(error_position("(1 + 2"), 6)
        self.assertEqual(error_position("max(1, 2"), 8)

    def test_unexpected_tokens(self):
        self.assertEqual(error_position("1 + 2)"), 5)
        self.assertEqual(error_position("2 3"), 2)
        self.assertEqual(error_position("1 * * 2"), 4)
        self.assertEqual(error_position("min(1,)"), 6)
        self.assertEqual(error_position("1, 2"), 1)
        self.assertEqual(error_position("()"), 1)

    def test_no_implicit_multiplication(self):
        self.assertEqual(error_position("2x", {"x": 1}), 1)
        self.assertEqual(error_position("2(3)"), 1)
        self.assertEqual(error_position("(1)(2)"), 3)

    def test_unexpected_characters(self):
        self.assertEqual(error_position("3 $ 4"), 2)
        self.assertEqual(error_position("5."), 1)
        self.assertEqual(error_position("2e"), 1)

    def test_syntax_error_wins_over_evaluation_error(self):
        self.assertEqual(error_position("1/0 +"), 5)
        self.assertEqual(error_position("nope + (1"), 9)


class EvaluationErrorPositionTest(unittest.TestCase):
    def test_unknown_names(self):
        self.assertEqual(error_position("1 + width"), 4)
        self.assertEqual(error_position("sqrt + 1"), 0)

    def test_unknown_function_and_arity(self):
        self.assertEqual(error_position("2 * foo(1)"), 4)
        self.assertEqual(error_position("1 + f(2)", {"f": 3}), 4)
        self.assertEqual(error_position("1 + hypot(3)"), 4)
        self.assertEqual(error_position("min()"), 0)
        self.assertEqual(error_position("sqrt(1, 2)"), 0)

    def test_arity_checked_before_arguments(self):
        self.assertEqual(error_position("abs(1, missing)"), 0)

    def test_function_failure(self):
        self.assertEqual(error_position("1 + sqrt(-1)"), 4)

    def test_division_by_zero(self):
        self.assertEqual(error_position("4 / (2 - 2)"), 2)
        self.assertEqual(error_position("5 % 0"), 2)

    def test_power_errors(self):
        self.assertEqual(error_position("1 + 0 ^ -1"), 6)
        self.assertEqual(error_position("(-8) ^ (1/3)"), 5)
        self.assertEqual(error_position("10^400"), 2)

    def test_left_to_right_order(self):
        self.assertEqual(error_position("a / 0", {}), 0)
        self.assertEqual(error_position("1 / 0 + a"), 2)
        self.assertEqual(error_position("max(x, 1/0)"), 4)
        self.assertEqual(error_position("max(1, 1/0, y)"), 8)

    def test_position_attribute_on_exception(self):
        with self.assertRaises(ExprError) as ctx:
            evaluate("1 + ")
        self.assertEqual(ctx.exception.position, 4)
