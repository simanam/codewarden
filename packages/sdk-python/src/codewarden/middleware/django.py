"""Django Middleware for CodeWarden.

Provides automatic error tracking and request context for Django applications.

Add to MIDDLEWARE in settings.py:
    MIDDLEWARE = [
        ...
        'codewarden.middleware.django.DjangoMiddleware',
        ...
    ]

Configure in settings.py:
    CODEWARDEN = {
        'DSN': 'https://key@ingest.codewarden.io/123',
        'ENVIRONMENT': 'production',
        'DEBUG': False,
        'EXCLUDED_PATHS': ['/health/', '/metrics/'],
        'CAPTURE_REQUEST_BODY': False,
    }
"""

from __future__ import annotations

import os
import time
import uuid
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

import codewarden
from codewarden.middleware.base import BaseMiddleware


class DjangoMiddleware(BaseMiddleware):
    """Django middleware for CodeWarden integration.

    This middleware captures exceptions, tracks request context,
    and provides automatic error reporting.

    Usage:
        Add 'codewarden.middleware.django.DjangoMiddleware' to MIDDLEWARE
        in your Django settings.
    """

    _initialized = False

    def __init__(self, get_response: Callable[["HttpRequest"], "HttpResponse"]):
        """Initialize Django middleware.

        Args:
            get_response: The next middleware or view callable
        """
        super().__init__()
        self.get_response = get_response
        self._init_codewarden()

    def _init_codewarden(self) -> None:
        """Initialize CodeWarden client from Django settings."""
        if DjangoMiddleware._initialized:
            return

        try:
            from django.conf import settings

            config = getattr(settings, "CODEWARDEN", {})

            dsn = config.get("DSN") or os.environ.get("CODEWARDEN_DSN")
            if dsn:
                codewarden.init(
                    dsn=dsn,
                    environment=config.get("ENVIRONMENT", os.environ.get("DJANGO_ENV", "production")),
                    debug=config.get("DEBUG", settings.DEBUG),
                )
                DjangoMiddleware._initialized = True

        except Exception:
            pass

    def __call__(self, request: "HttpRequest") -> "HttpResponse":
        """Process a request through the middleware.

        Args:
            request: Django HttpRequest object

        Returns:
            HttpResponse from the view or error handler
        """
        # Check if path should be excluded
        if self._should_exclude(request.path):
            return self.get_response(request)

        # Generate request ID
        request_id = str(uuid.uuid4())
        request.codewarden_request_id = request_id  # type: ignore
        request.codewarden_start_time = time.time()  # type: ignore

        # Set request context
        self._set_context(request)

        try:
            response = self.get_response(request)

            # Track response
            self._track_response(request, response)

            return response

        except Exception as e:
            # Capture exception
            self._capture_exception(e, request)
            raise

    def process_exception(
        self,
        request: "HttpRequest",
        exception: Exception,
    ) -> Optional["HttpResponse"]:
        """Process an exception that occurred during view execution.

        Args:
            request: Django HttpRequest object
            exception: The exception that was raised

        Returns:
            None to continue with default exception handling
        """
        self._capture_exception(exception, request)
        return None

    def _should_exclude(self, path: str) -> bool:
        """Check if path should be excluded from tracking."""
        try:
            from django.conf import settings

            config = getattr(settings, "CODEWARDEN", {})
            excluded = config.get("EXCLUDED_PATHS", ["/health/", "/healthz/", "/ready/", "/metrics/"])

            return any(path.startswith(p) for p in excluded)
        except Exception:
            return False

    def _set_context(self, request: "HttpRequest") -> None:
        """Set CodeWarden context from request."""
        try:
            client = codewarden.get_client()

            context = {
                "request_id": getattr(request, "codewarden_request_id", None),
                "url": request.build_absolute_uri(),
                "method": request.method,
                "path": request.path,
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "ip_address": self._get_client_ip(request),
            }

            # Add user info if authenticated
            if hasattr(request, "user") and request.user.is_authenticated:
                context["user_id"] = str(request.user.pk)
                if hasattr(request.user, "email"):
                    context["user_email"] = request.user.email

            client.setContext(context)

        except Exception:
            pass

    def _get_client_ip(self, request: "HttpRequest") -> str:
        """Get client IP address from request."""
        # Check forwarded headers
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        x_real_ip = request.META.get("HTTP_X_REAL_IP")
        if x_real_ip:
            return x_real_ip

        return request.META.get("REMOTE_ADDR", "")

    def _track_response(
        self,
        request: "HttpRequest",
        response: "HttpResponse",
    ) -> None:
        """Track response metrics."""
        start_time = getattr(request, "codewarden_start_time", None)
        if not start_time:
            return

        duration = time.time() - start_time
        status_code = response.status_code

        # Log slow requests
        if duration > 5.0:
            try:
                client = codewarden.get_client()
                client.capture_message(
                    f"Slow request: {request.method} {request.path} took {duration:.2f}s",
                    level="warning",
                )
            except Exception:
                pass

        # Log server errors
        if status_code >= 500:
            try:
                client = codewarden.get_client()
                client.capture_message(
                    f"Server error {status_code}: {request.method} {request.path}",
                    level="error",
                )
            except Exception:
                pass

        # Track in evidence for compliance
        if status_code >= 400 or duration > 5.0:
            try:
                from codewarden.evidence import log_access

                log_access(
                    action="request",
                    resource=f"{request.method} {request.path}",
                    success=status_code < 400,
                    ip_address=self._get_client_ip(request),
                    metadata={
                        "status_code": status_code,
                        "duration_ms": int(duration * 1000),
                    },
                )
            except Exception:
                pass

    def _capture_exception(
        self,
        exception: Exception,
        request: "HttpRequest",
    ) -> None:
        """Capture and report an exception."""
        try:
            client = codewarden.get_client()

            # Set extra context
            client.setContext({
                "request_id": getattr(request, "codewarden_request_id", None),
                "url": request.build_absolute_uri(),
                "method": request.method,
                "path": request.path,
            })

            client.capture_exception(exception)

        except Exception:
            pass


def capture_exception(view_func: Callable) -> Callable:
    """Decorator to capture exceptions from a Django view.

    Example:
        >>> from codewarden.middleware.django import capture_exception
        >>>
        >>> @capture_exception
        >>> def my_view(request):
        ...     # Your code here
        ...     pass
    """
    from functools import wraps

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            try:
                client = codewarden.get_client()
                client.capture_exception(e)
            except Exception:
                pass
            raise

    return wrapper


def get_request_id(request: "HttpRequest") -> Optional[str]:
    """Get the CodeWarden request ID from a Django request.

    Args:
        request: Django HttpRequest object

    Returns:
        Request ID string or None

    Example:
        >>> from codewarden.middleware.django import get_request_id
        >>> request_id = get_request_id(request)
    """
    return getattr(request, "codewarden_request_id", None)
