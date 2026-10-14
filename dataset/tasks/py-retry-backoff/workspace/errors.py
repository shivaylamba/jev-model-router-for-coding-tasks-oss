"""Errors raised by transports."""


class TransportError(Exception):
    """Base class for transport failures."""


class TransientError(TransportError):
    """A failure worth retrying: timeouts, 502/503/504, connection resets."""


class PermanentError(TransportError):
    """A failure that will not go away on retry: 4xx responses, bad payloads."""
