"""Errors shared by the service and API layers."""


class ValidationError(ValueError):
    """A request parameter is invalid. The API turns it into a 400 response."""
