"""CodeWarden Base Middleware - Abstract base class for framework middleware."""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Callable

import codewarden
from codewarden.types import EventContext


class BaseMiddleware(ABC):
    """
    Abstract base class for framework-specific middleware.

    Provides common functionality for request tracking, error capture,
    and context management across different web frameworks.
    """

    def __init__(
        self,
        *,
        capture_exceptions: bool = True,
        capture_request_body: bool = False,
        capture_response_body: bool = False,
        excluded_paths: list[str] | None = None,
        max_body_size: int = 10240,  # 10KB
    ) -> None:
        """
        Initialize base middleware.

        Args:
            capture_exceptions: Automatically capture unhandled exceptions
            capture_request_body: Include request body in context
            capture_response_body: Include response body in context
            excluded_paths: Paths to exclude from tracking (e.g., ["/health", "/metrics"])
            max_body_size: Maximum body size to capture in bytes
        """
        self._capture_exceptions = capture_exceptions
        self._capture_request_body = capture_request_body
        self._capture_response_body = capture_response_body
        self._excluded_paths = excluded_paths or []
        self._max_body_size = max_body_size

    def should_track_request(self, path: str) -> bool:
        """
        Determine if a request should be tracked.

        Args:
            path: The request path

        Returns:
            True if the request should be tracked
        """
        # Skip excluded paths
        for excluded in self._excluded_paths:
            if path.startswith(excluded):
                return False
        return True

    def generate_request_id(self) -> str:
        """Generate a unique request ID."""
        return str(uuid.uuid4())

    def build_request_context(
        self,
        *,
        request_id: str,
        method: str,
        path: str,
        query_string: str | None = None,
        headers: dict[str, str] | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> EventContext:
        """
        Build a request context dictionary.

        Args:
            request_id: Unique request identifier
            method: HTTP method
            path: Request path
            query_string: Query string parameters
            headers: Request headers (filtered)
            client_ip: Client IP address
            user_agent: User agent string

        Returns:
            EventContext with request information
        """
        context: EventContext = {
            "request_id": request_id,
        }

        # Add optional fields
        if client_ip:
            context["ip_address"] = client_ip
        if user_agent:
            context["user_agent"] = user_agent

        return context

    def capture_exception(
        self,
        exception: BaseException,
        context: EventContext | None = None,
    ) -> str | None:
        """
        Capture an exception if enabled.

        Args:
            exception: The exception to capture
            context: Additional context to include

        Returns:
            Event ID if captured, None otherwise
        """
        if not self._capture_exceptions:
            return None

        try:
            client = codewarden.get_client()
            if context:
                client.set_context(context)
            return client.capture_exception(exception)
        except Exception:
            # Don't let SDK errors crash the app
            return None

    def truncate_body(self, body: bytes | str) -> str:
        """
        Truncate body to max size and convert to string.

        Args:
            body: Request or response body

        Returns:
            Truncated body as string
        """
        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="replace")

        if len(body) > self._max_body_size:
            return body[: self._max_body_size] + "... [truncated]"
        return body

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Process a request through the middleware."""
        pass


class RequestTimer:
    """Context manager for timing requests."""

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def __enter__(self) -> "RequestTimer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self.end_time = time.perf_counter()

    @property
    def duration_ms(self) -> float:
        """Get request duration in milliseconds."""
        return (self.end_time - self.start_time) * 1000
