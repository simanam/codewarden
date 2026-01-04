"""CodeWarden Client - Main SDK client class."""

from __future__ import annotations

import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

from codewarden.airlock import Airlock
from codewarden.transport import Transport
from codewarden.types import Event, EventContext, ExceptionInfo, StackFrame


class CodeWardenClient:
    """Main CodeWarden SDK client."""

    def __init__(
        self,
        dsn: str,
        *,
        environment: str = "production",
        release: str | None = None,
        enable_pii_scrubbing: bool = True,
        debug: bool = False,
    ) -> None:
        """
        Initialize the CodeWarden client.

        Args:
            dsn: Data Source Name for event ingestion
            environment: Environment name
            release: Release/version identifier
            enable_pii_scrubbing: Enable PII scrubbing
            debug: Enable debug mode
        """
        self._dsn = dsn
        self._environment = environment
        self._release = release
        self._enable_pii_scrubbing = enable_pii_scrubbing
        self._debug = debug

        self._transport = Transport(dsn, debug=debug)
        self._airlock = Airlock() if enable_pii_scrubbing else None
        self._context: EventContext = {}

    def set_context(self, context: EventContext) -> None:
        """Set additional context for events."""
        self._context.update(context)

    def set_user(
        self,
        user_id: str | None = None,
        email: str | None = None,
        username: str | None = None,
    ) -> None:
        """Set user context for events."""
        if user_id:
            self._context["user_id"] = user_id
        if email:
            self._context["email"] = email
        if username:
            self._context["username"] = username

    def capture_exception(self, exception: BaseException) -> str:
        """
        Capture and send an exception.

        Args:
            exception: The exception to capture

        Returns:
            Event ID
        """
        event = self._build_event(
            level="error",
            message=str(exception),
            exception=exception,
        )
        return self._send_event(event)

    def capture_message(self, message: str, level: str = "info") -> str:
        """
        Capture and send a message.

        Args:
            message: The message to capture
            level: Log level (error, warning, info, debug)

        Returns:
            Event ID
        """
        event = self._build_event(level=level, message=message)
        return self._send_event(event)

    def _build_event(
        self,
        level: str,
        message: str,
        exception: BaseException | None = None,
    ) -> Event:
        """Build an event payload."""
        event: Event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,  # type: ignore[typeddict-item]
            "message": message,
            "context": dict(self._context),
            "tags": {},
            "extra": {},
            "environment": self._environment,
            "release": self._release,
        }

        if exception:
            event["exception"] = self._parse_exception(exception)

        # Scrub PII if enabled
        if self._airlock:
            event = self._airlock.scrub_event(event)

        return event

    def _parse_exception(self, exception: BaseException) -> ExceptionInfo:
        """Parse an exception into structured format."""
        tb = traceback.extract_tb(exception.__traceback__)
        frames: list[StackFrame] = []

        for frame in tb:
            frames.append(
                {
                    "filename": frame.filename,
                    "lineno": frame.lineno,
                    "function": frame.name,
                    "context_line": frame.line,
                    "pre_context": [],
                    "post_context": [],
                }
            )

        return {
            "type": type(exception).__name__,
            "value": str(exception),
            "module": type(exception).__module__,
            "stacktrace": frames,
        }

    def _send_event(self, event: Event) -> str:
        """Send an event to CodeWarden."""
        self._transport.send(event)
        return event["event_id"]

    def flush(self) -> None:
        """Flush all pending events."""
        self._transport.flush()

    def close(self) -> None:
        """Close the client and flush pending events."""
        self.flush()
        self._transport.close()
