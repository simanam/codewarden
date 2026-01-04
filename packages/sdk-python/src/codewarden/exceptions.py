"""CodeWarden SDK Exceptions."""


class CodeWardenError(Exception):
    """Base exception for CodeWarden SDK."""

    pass


class ConfigurationError(CodeWardenError):
    """Raised when the SDK is not properly configured."""

    pass


class TransportError(CodeWardenError):
    """Raised when there's an error sending events."""

    pass
