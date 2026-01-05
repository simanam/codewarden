"""CodeWarden FastAPI Middleware - ASGI middleware for FastAPI applications."""

from __future__ import annotations

import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

import codewarden
from codewarden.middleware.base import BaseMiddleware, RequestTimer
from codewarden.types import EventContext

logger = logging.getLogger(__name__)


class CodeWardenMiddleware(BaseHTTPMiddleware, BaseMiddleware):
    """
    FastAPI/Starlette middleware for CodeWarden integration.

    Automatically captures:
    - Unhandled exceptions with full context
    - Request/response metadata
    - Request timing information

    Example:
        >>> from fastapi import FastAPI
        >>> from codewarden.middleware import FastAPIMiddleware
        >>>
        >>> app = FastAPI()
        >>> app.add_middleware(
        ...     FastAPIMiddleware,
        ...     capture_exceptions=True,
        ...     excluded_paths=["/health", "/metrics"],
        ... )
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        capture_exceptions: bool = True,
        capture_request_body: bool = False,
        capture_response_body: bool = False,
        excluded_paths: list[str] | None = None,
        max_body_size: int = 10240,
    ) -> None:
        """
        Initialize FastAPI middleware.

        Args:
            app: The ASGI application
            capture_exceptions: Automatically capture unhandled exceptions
            capture_request_body: Include request body in context (caution: PII)
            capture_response_body: Include response body in context
            excluded_paths: Paths to exclude from tracking
            max_body_size: Maximum body size to capture in bytes
        """
        # Initialize Starlette middleware
        BaseHTTPMiddleware.__init__(self, app)

        # Initialize CodeWarden base middleware
        BaseMiddleware.__init__(
            self,
            capture_exceptions=capture_exceptions,
            capture_request_body=capture_request_body,
            capture_response_body=capture_response_body,
            excluded_paths=excluded_paths,
            max_body_size=max_body_size,
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """
        Process an incoming request.

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            The response
        """
        # Check if we should track this request
        if not self.should_track_request(request.url.path):
            return await call_next(request)

        # Generate request ID
        request_id = self.generate_request_id()

        # Build request context
        context = self._build_fastapi_context(request, request_id)

        # Set context on client
        try:
            client = codewarden.get_client()
            client.set_context(context)
        except Exception:
            # SDK not initialized, continue without tracking
            pass

        # Add request ID to response headers
        with RequestTimer() as timer:
            try:
                response = await call_next(request)
            except Exception as exc:
                # Capture exception with request context
                self._handle_exception(exc, request, context, timer)
                raise

        # Add request ID header
        response.headers["X-Request-ID"] = request_id

        # Log slow requests
        if timer.duration_ms > 1000:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {timer.duration_ms:.2f}ms"
            )

        return response

    def _build_fastapi_context(
        self,
        request: Request,
        request_id: str,
    ) -> EventContext:
        """
        Build context from a FastAPI request.

        Args:
            request: The FastAPI request
            request_id: The generated request ID

        Returns:
            EventContext with request information
        """
        # Extract client IP (handle proxies)
        client_ip = self._get_client_ip(request)

        # Extract user agent
        user_agent = request.headers.get("user-agent")

        # Build base context
        context = self.build_request_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_string=str(request.url.query) if request.url.query else None,
            client_ip=client_ip,
            user_agent=user_agent,
        )

        return context

    def _get_client_ip(self, request: Request) -> str | None:
        """
        Extract client IP from request, handling proxies.

        Args:
            request: The FastAPI request

        Returns:
            Client IP address or None
        """
        # Check X-Forwarded-For header first (for proxied requests)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return None

    def _handle_exception(
        self,
        exc: Exception,
        request: Request,
        context: EventContext,
        timer: RequestTimer,
    ) -> None:
        """
        Handle an exception during request processing.

        Args:
            exc: The exception
            request: The request that caused the exception
            context: Current request context
            timer: Request timer for duration
        """
        # Capture with enhanced context
        event_id = self.capture_exception(exc, context)

        if event_id:
            logger.info(
                f"Captured exception {type(exc).__name__} "
                f"for {request.method} {request.url.path} "
                f"[event_id={event_id}]"
            )
