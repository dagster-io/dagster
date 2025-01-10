class DgError(Exception):
    """Base class for errors thrown by the dg CLI."""

    pass


class DgValidationError(DgError):
    """Error raised when a configuration file fails validation."""

    pass
