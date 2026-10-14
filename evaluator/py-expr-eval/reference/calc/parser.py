"""Recursive-descent parser producing a small AST."""

from dataclasses import dataclass

from calc.errors import ExprError
from calc.lexer import tokenize


@dataclass(frozen=True)
class Num:
    value: float
    pos: int


@dataclass(frozen=True)
class Name:
    name: str
    pos: int


@dataclass(frozen=True)
class Call:
    name: str
    args: tuple
    pos: int


@dataclass(frozen=True)
class Unary:
    op: str
    operand: object
    pos: int


@dataclass(frozen=True)
class Binary:
    op: str
    left: object
    right: object
    pos: int


class _Parser:
    def __init__(self, expr):
        self.tokens = tokenize(expr)
        self.index = 0

    @property
    def current(self):
        return self.tokens[self.index]

    def advance(self):
        token = self.current
        self.index += 1
        return token

    def at(self, *ops):
        return self.current.kind == "op" and self.current.text in ops

    def fail(self, message):
        raise ExprError(message, self.current.pos)

    def parse(self):
        node = self.additive()
        if self.current.kind != "end":
            self.fail(f"unexpected {self.current.text!r}")
        return node

    def additive(self):
        node = self.multiplicative()
        while self.at("+", "-"):
            op = self.advance()
            node = Binary(op.text, node, self.multiplicative(), op.pos)
        return node

    def multiplicative(self):
        node = self.unary()
        while self.at("*", "/", "%"):
            op = self.advance()
            node = Binary(op.text, node, self.unary(), op.pos)
        return node

    def unary(self):
        if self.at("+", "-"):
            op = self.advance()
            return Unary(op.text, self.unary(), op.pos)
        return self.power()

    def power(self):
        base = self.primary()
        if self.at("^"):
            op = self.advance()
            return Binary("^", base, self.unary(), op.pos)
        return base

    def primary(self):
        token = self.current
        if token.kind == "num":
            self.advance()
            return Num(float(token.text), token.pos)
        if token.kind == "name":
            self.advance()
            if self.at("("):
                self.advance()
                args = []
                if not self.at(")"):
                    args.append(self.additive())
                    while self.at(","):
                        self.advance()
                        args.append(self.additive())
                if not self.at(")"):
                    self.fail("expected ')'")
                self.advance()
                return Call(token.text, tuple(args), token.pos)
            return Name(token.text, token.pos)
        if self.at("("):
            self.advance()
            node = self.additive()
            if not self.at(")"):
                self.fail("expected ')'")
            self.advance()
            return node
        if token.kind == "end":
            self.fail("unexpected end of formula")
        self.fail(f"expected a value, found {token.text!r}")


def parse(expr):
    return _Parser(expr).parse()
