class ValidationError(ValueError):
    """A submitted value is invalid. `field` names the input that was rejected."""

    def __init__(self, field, message):
        super().__init__(f"{field}: {message}")
        self.field = field
        self.message = message
