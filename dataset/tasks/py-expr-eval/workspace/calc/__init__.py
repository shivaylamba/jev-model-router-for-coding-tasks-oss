"""Formula engine for computed columns. See SPEC.md."""

from calc.errors import ExprError

__all__ = ["ExprError", "evaluate"]


def evaluate(expr, variables=None):
    """Evaluate the formula `expr` and return a float (see SPEC.md).

    `variables` maps names to int or float values. Raises ExprError, with a
    `position`, for any syntax or evaluation error.
    """
    raise NotImplementedError
