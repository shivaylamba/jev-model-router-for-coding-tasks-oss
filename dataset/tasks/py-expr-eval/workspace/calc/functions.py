"""Built-in functions and constants available to formulas."""

import math

# name -> (min_args, max_args or None for unlimited, implementation)
FUNCTIONS = {
    "abs": (1, 1, abs),
    "sqrt": (1, 1, math.sqrt),
    "min": (1, None, min),
    "max": (1, None, max),
    "round": (1, 1, round),
    "hypot": (2, 2, math.hypot),
}

CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def arity_ok(name, count):
    """Whether FUNCTIONS[name] accepts `count` arguments."""
    low, high, _ = FUNCTIONS[name]
    return count >= low and (high is None or count <= high)
