"""Tokenizer for the formula language."""

import re
from dataclasses import dataclass

from calc.errors import ExprError

_NUMBER = re.compile(r"(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?")
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_SINGLE = set("+-*/%^(),")


@dataclass(frozen=True)
class Token:
    kind: str  # "num", "name", "op" (operators and punctuation) or "end"
    text: str
    pos: int


def tokenize(expr):
    tokens = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch in " \t":
            i += 1
            continue
        match = _NUMBER.match(expr, i)
        if match:
            tokens.append(Token("num", match.group(), i))
            i = match.end()
            continue
        match = _NAME.match(expr, i)
        if match:
            tokens.append(Token("name", match.group(), i))
            i = match.end()
            continue
        if ch in _SINGLE:
            tokens.append(Token("op", ch, i))
            i += 1
            continue
        raise ExprError(f"unexpected character {ch!r}", i)
    tokens.append(Token("end", "", len(expr)))
    return tokens
