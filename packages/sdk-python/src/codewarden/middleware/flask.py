"""Flask Middleware for CodeWarden.

Provides automatic error tracking and request context for Flask applications.

Example:
    >>> from flask import Flask
    >>> from codewarden.middleware import init_flask
    >>>
    >>> app = Flask(__name__)
    >>> init_flask(app)
"""

from __future__ import annotations

import time
import traceback
import uuid
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from flask import Flask, Request, Response

import codewarden
from codewarden.middleware.base import BaseMiddleware


class FlaskMiddleware(BaseMiddleware):
    """WSGI middleware for Flask applications.

    This middleware wraps the Flask application to capture exceptions
    and add request context to events.

    Example:
        >>> from flask import Flask
        >>> from codewarden.middleware.flask import FlaskMiddleware
        >>>
        >>> app = Flask(__name__)
        >>> app.wsgi_app = FlaskMiddleware(app.wsgi_app, app)
    """

    def __init__(
        self,
        wsgi_app: Any,
        flask_app: "Flask",
        capture_request_body: bool = False,
        capture_response_body: bool = False,
        excluded_paths: Optional[list[str]] = None,
    ):
        """Initialize Flask middleware.

        Args:
            wsgi_app: The WSGI application to wrap
            flask_app: The Flask application instance
            capture_request_body: Whether to capture request bodies
            capture_response_body: Whether to capture response bodies
            excluded_paths: Paths to exclude from tracking
        """
        super().__init__()
        self.wsgi_app = wsgi_app
        self.flask_app = flask_app
        self.capture_request_body = capture_request_body
        self.capture_response_body = capture_response_body
        self.excluded_paths = excluded_paths or ["/health", "/healthz", "/ready", "/metrics"]

    def __call__(self, environ: dict, start_response: Callable) -> Any:
        """Handle WSGI request."""
        path = environ.get("PATH_INFO", "")

        # Skip excluded paths
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return self.wsgi_app(environ, start_response)

        # Generate request ID
        request_id = str(uuid.uuid4())
        environ["codewarden.request_id"] = request_id

        # Extract request context
        context = self._extract_context(environ)
        context["request_id"] = request_id

        # Set context on the client
        try:
            client = codewarden.get_client()
            # We would need to use a context variable here for thread safety
            # For now, set global context (not thread-safe for concurrent requests)
        except Exception:
            pass

        start_time = time.time()
        status_code = 500
        response_headers: list = []

        def custom_start_response(status: str, headers: list, exc_info=None):
            nonlocal status_code, response_headers
            status_code = int(status.split(" ")[0])
            response_headers = headers
            return start_response(status, headers, exc_info)

        try:
            response = self.wsgi_app(environ, custom_start_response)
            return response

        except Exception as e:
            # Capture the exception
            try:
                client = codewarden.get_client()
                client.capture_exception(e)
            except Exception:
                pass

            # Re-raise to let Flask handle it
            raise

        finally:
            # Track request duration
            duration = time.time() - start_time
            self._track_request(path, environ.get("REQUEST_METHOD", "GET"), status_code, duration)

    def _extract_context(self, environ: dict) -> dict[str, Any]:
        """Extract context from WSGI environ."""
        return {
            "url": self._build_url(environ),
            "method": environ.get("REQUEST_METHOD", "GET"),
            "path": environ.get("PATH_INFO", ""),
            "query_string": environ.get("QUERY_STRING", ""),
            "user_agent": environ.get("HTTP_USER_AGENT", ""),
            "ip_address": self._get_client_ip(environ),
            "host": environ.get("HTTP_HOST", ""),
        }

    def _build_url(self, environ: dict) -> str:
        """Build URL from WSGI environ."""
        scheme = environ.get("wsgi.url_scheme", "http")
        host = environ.get("HTTP_HOST", environ.get("SERVER_NAME", "localhost"))
        path = environ.get("PATH_INFO", "/")
        query = environ.get("QUERY_STRING", "")

        url = f"{scheme}://{host}{path}"
        if query:
            url += f"?{query}"

        return url

    def _get_client_ip(self, environ: dict) -> str:
        """Get client IP from WSGI environ."""
        # Check forwarded headers first
        forwarded = environ.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = environ.get("HTTP_X_REAL_IP")
        if real_ip:
            return real_ip

        return environ.get("REMOTE_ADDR", "")

    def _track_request(
        self,
        path: str,
        method: str,
        status_code: int,
        duration: float,
    ) -> None:
        """Track request metrics (optional integration with evidence)."""
        # Could send to evidence collector for slow requests or errors
        if status_code >= 500 or duration > 5.0:
            try:
                from codewarden.evidence import log_access

                log_access(
                    action="request",
                    resource=f"{method} {path}",
                    success=status_code < 400,
                    metadata={
                        "status_code": status_code,
                        "duration_ms": int(duration * 1000),
                    },
                )
            except Exception:
                pass


def init_flask(
    app: "Flask",
    dsn: Optional[str] = None,
    capture_request_body: bool = False,
    capture_response_body: bool = False,
    excluded_paths: Optional[list[str]] = None,
) -> None:
    """Initialize CodeWarden for a Flask application.

    This is the recommended way to integrate CodeWarden with Flask.
    It sets up:
    - Exception capture via error handlers
    - Request context tracking
    - Automatic breadcrumbs for requests

    Args:
        app: Flask application instance
        dsn: CodeWarden DSN (or set CODEWARDEN_DSN env var)
        capture_request_body: Whether to capture request bodies
        capture_response_body: Whether to capture response bodies
        excluded_paths: Paths to exclude from tracking

    Example:
        >>> from flask import Flask
        >>> from codewarden.middleware import init_flask
        >>>
        >>> app = Flask(__name__)
        >>> init_flask(app, dsn="https://key@ingest.codewarden.io/123")
    """
    import os

    # Initialize CodeWarden client
    dsn = dsn or os.environ.get("CODEWARDEN_DSN")
    if dsn:
        codewarden.init(
            dsn=dsn,
            environment=os.environ.get("FLASK_ENV", "production"),
            debug=app.debug,
        )

    # Install WSGI middleware
    app.wsgi_app = FlaskMiddleware(
        app.wsgi_app,
        app,
        capture_request_body=capture_request_body,
        capture_response_body=capture_response_body,
        excluded_paths=excluded_paths,
    )

    # Register error handlers
    @app.errorhandler(Exception)
    def handle_exception(error: Exception):
        """Capture unhandled exceptions."""
        try:
            client = codewarden.get_client()
            client.capture_exception(error)
        except Exception:
            pass

        # Re-raise to use Flask's default error handling
        raise error

    # Before request hook to set context
    @app.before_request
    def before_request():
        """Set request context before each request."""
        from flask import g, request

        g.codewarden_request_id = str(uuid.uuid4())
        g.codewarden_start_time = time.time()

        try:
            client = codewarden.get_client()
            client.setContext({
                "request_id": g.codewarden_request_id,
                "url": request.url,
                "method": request.method,
                "path": request.path,
                "user_agent": request.user_agent.string,
                "ip_address": request.remote_addr,
            })
        except Exception:
            pass

    # After request hook to clear context
    @app.after_request
    def after_request(response):
        """Track request completion."""
        from flask import g

        # Calculate duration
        if hasattr(g, "codewarden_start_time"):
            duration = time.time() - g.codewarden_start_time

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

        return response


def capture_exception(func: Callable) -> Callable:
    """Decorator to capture exceptions from a route.

    Example:
        >>> from codewarden.middleware.flask import capture_exception
        >>>
        >>> @app.route("/api/data")
        >>> @capture_exception
        >>> def get_data():
        ...     # Your code here
        ...     pass
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            try:
                client = codewarden.get_client()
                client.capture_exception(e)
            except Exception:
                pass
            raise

    return wrapper
