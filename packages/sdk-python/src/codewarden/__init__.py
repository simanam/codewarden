"""
CodeWarden Python SDK.

A drop-in security and observability SDK for Python applications.

Example:
    >>> import codewarden
    >>> codewarden.init("https://key@ingest.codewarden.io/123")
    >>> codewarden.capture_message("Hello from CodeWarden!")
    >>>
    >>> # Add breadcrumbs for context
    >>> codewarden.add_breadcrumb("ui", "User clicked submit")
    >>>
    >>> # Run security scans
    >>> from codewarden import run_security_scan
    >>> result = run_security_scan("./src")
    >>> print(f"Found {result.total_count} security issues")
"""

from codewarden.client import CodeWardenClient
from codewarden.exceptions import CodeWardenError, ConfigurationError
from codewarden.watchdog import add_breadcrumb, get_watchdog

# Lazy import for scanners to avoid heavy dependencies
def run_security_scan(
    target_path: str = ".",
    scan_dependencies: bool = True,
    scan_secrets: bool = True,
    scan_code: bool = True,
):
    """Run security scans on the target path.

    Args:
        target_path: Directory to scan
        scan_dependencies: Run dependency vulnerability scan (pip-audit)
        scan_secrets: Run secret detection scan (Gitleaks patterns)
        scan_code: Run static code analysis (Bandit)

    Returns:
        ScanResult with all findings

    Example:
        >>> result = run_security_scan("./src")
        >>> for finding in result.findings:
        ...     print(f"{finding.severity}: {finding.title}")
    """
    from codewarden.scanners import run_security_scan as _run_scan
    return _run_scan(
        target_path=target_path,
        scan_dependencies=scan_dependencies,
        scan_secrets=scan_secrets,
        scan_code=scan_code,
    )


__version__ = "0.1.0"
__all__ = [
    # Core
    "init",
    "get_client",
    "capture_exception",
    "capture_message",
    "add_breadcrumb",
    "get_watchdog",
    "CodeWardenClient",
    "CodeWardenError",
    "ConfigurationError",
    # Security scanning
    "run_security_scan",
    # Version
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
