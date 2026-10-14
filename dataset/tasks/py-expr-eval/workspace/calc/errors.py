"""Errors raised by the formula engine."""


class ExprError(ValueError):
    """A formula could not be parsed or evaluated.

    `position` is a 0-based index into the original formula string pointing
    at the place the problem was found (see SPEC.md).
    """

    def __init__(self, message, position):
        super().__init__(f"{message} (at position {position})")
        self.message = message
        self.position = position
