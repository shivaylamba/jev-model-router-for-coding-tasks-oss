"""Formula engine for computed columns. See SPEC.md."""

import math

from calc.errors import ExprError
from calc.functions import CONSTANTS, FUNCTIONS, arity_ok
from calc.parser import Binary, Call, Name, Num, Unary, parse

__all__ = ["ExprError", "evaluate"]


def _power(base, exponent, pos):
    try:
        result = base ** exponent
    except (ZeroDivisionError, OverflowError) as exc:
        raise ExprError(f"invalid power: {exc}", pos) from None
    if isinstance(result, complex) or not math.isfinite(result):
        raise ExprError("power is not a finite real number", pos)
    return result


def _eval(node, variables):
    if isinstance(node, Num):
        return node.value
    if isinstance(node, Name):
        if node.name in variables:
            return float(variables[node.name])
        if node.name in CONSTANTS:
            return float(CONSTANTS[node.name])
        raise ExprError(f"unknown name {node.name!r}", node.pos)
    if isinstance(node, Call):
        if node.name not in FUNCTIONS:
            raise ExprError(f"unknown function {node.name!r}", node.pos)
        if not arity_ok(node.name, len(node.args)):
            raise ExprError(f"wrong number of arguments for {node.name}", node.pos)
        args = [_eval(arg, variables) for arg in node.args]
        try:
            return float(FUNCTIONS[node.name][2](*args))
        except (ValueError, ArithmeticError, TypeError) as exc:
            raise ExprError(f"{node.name} failed: {exc}", node.pos) from None
    if isinstance(node, Unary):
        value = _eval(node.operand, variables)
        return -value if node.op == "-" else value
    if isinstance(node, Binary):
        left = _eval(node.left, variables)
        right = _eval(node.right, variables)
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op in "/%":
            if right == 0:
                raise ExprError("division by zero", node.pos)
            return left / right if node.op == "/" else left % right
        return _power(left, right, node.pos)
    raise TypeError(f"unknown node {node!r}")


def evaluate(expr, variables=None):
    """Evaluate the formula `expr` and return a float (see SPEC.md).

    `variables` maps names to int or float values. Raises ExprError, with a
    `position`, for any syntax or evaluation error.
    """
    tree = parse(expr)
    return float(_eval(tree, variables or {}))
