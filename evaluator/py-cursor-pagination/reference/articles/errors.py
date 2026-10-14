"""Errors shared by the service and API layers."""


class ValidationError(ValueError):
    """A request parameter is invalid. The API turns it into a 400 response."""


class InvalidCursorError(ValidationError):
    """A pagination cursor is malformed or does not belong to this query."""
