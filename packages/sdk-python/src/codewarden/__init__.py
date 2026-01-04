"""
CodeWarden Python SDK.

A drop-in security and observability SDK for Python applications.

Example:
    >>> import codewarden
    >>> codewarden.init("https://key@ingest.codewarden.io/123")
    >>> codewarden.capture_message("Hello from CodeWarden!")
"""

from codewarden.client import CodeWardenClient
from codewarden.exceptions import CodeWardenError, ConfigurationError

__version__ = "0.1.0"
__all__ = [
    "init",
    "get_client",
    "capture_exception",
    "capture_message",
    "CodeWardenClient",
    "CodeWardenError",
    "ConfigurationError",
    "__version__",
]

# Global client instance
_client: CodeWardenClient | None = None


def init(
    dsn: str,
    *,
    environment: str = "production",
    release: str | None = None,
    enable_pii_scrubbing: bool = True,
    debug: bool = False,
) -> CodeWardenClient:
    """
    Initialize the CodeWarden SDK.

    Args:
        dsn: Your CodeWarden DSN (from dashboard)
        environment: Environment name (e.g., "production", "staging")
        release: Optional release/version identifier
        enable_pii_scrubbing: Enable automatic PII scrubbing (default: True)
        debug: Enable debug logging (default: False)

    Returns:
        Configured CodeWardenClient instance

    Example:
        >>> import codewarden
        >>> codewarden.init("https://key@ingest.codewarden.io/123")
    """
    global _client
    _client = CodeWardenClient(
        dsn=dsn,
        environment=environment,
        release=release,
        enable_pii_scrubbing=enable_pii_scrubbing,
        debug=debug,
    )
    return _client


def get_client() -> CodeWardenClient:
    """Get the initialized client instance."""
    if _client is None:
        raise ConfigurationError(
            "CodeWarden SDK not initialized. Call codewarden.init() first."
        )
    return _client


def capture_exception(exception: BaseException) -> str:
    """Capture and send an exception to CodeWarden."""
    return get_client().capture_exception(exception)


def capture_message(message: str, level: str = "info") -> str:
    """Capture and send a message to CodeWarden."""
    return get_client().capture_message(message, level=level)
