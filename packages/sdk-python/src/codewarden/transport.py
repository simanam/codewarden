"""CodeWarden Transport - HTTP transport layer."""

from __future__ import annotations

import atexit
import logging
import queue
import threading
from typing import Any
from urllib.parse import urlparse

import httpx

from codewarden.exceptions import ConfigurationError
from codewarden.types import Event

logger = logging.getLogger(__name__)


def parse_dsn(dsn: str) -> tuple[str, str]:
    """
    Parse a CodeWarden DSN into base URL and API key.

    DSN format: https://API_KEY@host/path or just https://host/path with separate API key

    Examples:
        - https://cw_live_abc123@api.codewarden.io/v1/telemetry
        - https://cw_live_abc123@localhost:8000/v1/telemetry
        - https://api.codewarden.io/v1/telemetry (API key in URL or separate)

    Args:
        dsn: The Data Source Name string

    Returns:
        Tuple of (base_url, api_key)

    Raises:
        ConfigurationError: If DSN is invalid
    """
    if not dsn:
        raise ConfigurationError("DSN cannot be empty")

    parsed = urlparse(dsn)

    # Extract API key from URL if present (username part)
    api_key = parsed.username or ""

    # Build base URL without credentials
    if parsed.username:
        # Rebuild URL without the username (API key)
        netloc = parsed.hostname or ""
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        base_url = f"{parsed.scheme}://{netloc}"
    else:
        base_url = f"{parsed.scheme}://{parsed.netloc}"

    return base_url, api_key


class Transport:
    """HTTP transport for sending events to CodeWarden."""

    def __init__(
        self,
        dsn: str,
        *,
        max_queue_size: int = 100,
        batch_size: int = 10,
        flush_interval: float = 5.0,
        timeout: float = 30.0,
        max_retries: int = 3,
        debug: bool = False,
    ) -> None:
        """
        Initialize the transport.

        Args:
            dsn: Data Source Name (e.g., https://API_KEY@api.codewarden.io)
            max_queue_size: Maximum events to queue
            batch_size: Events per batch
            flush_interval: Seconds between flushes
            timeout: HTTP timeout in seconds
            max_retries: Maximum retry attempts
            debug: Enable debug logging
        """
        self._base_url, self._api_key = parse_dsn(dsn)
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._timeout = timeout
        self._max_retries = max_retries
        self._debug = debug

        self._queue: queue.Queue[Event] = queue.Queue(maxsize=max_queue_size)
        self._shutdown = threading.Event()
        self._client = httpx.Client(timeout=timeout)

        # Start background worker
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

        # Register cleanup on exit
        atexit.register(self.close)

    def send(self, event: Event) -> None:
        """
        Queue an event for sending.

        Args:
            event: The event to send
        """
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            if self._debug:
                logger.warning("Event queue full, dropping event")

    def flush(self) -> None:
        """Flush all pending events."""
        events: list[Event] = []
        while True:
            try:
                event = self._queue.get_nowait()
                events.append(event)
            except queue.Empty:
                break

        for event in events:
            self._send_event(event)

    def close(self) -> None:
        """Close the transport and flush pending events."""
        self._shutdown.set()
        self.flush()
        self._client.close()

    def _worker_loop(self) -> None:
        """Background worker that sends events."""
        while not self._shutdown.is_set():
            try:
                # Wait for event with timeout
                event = self._queue.get(timeout=self._flush_interval)
                self._send_event(event)
            except queue.Empty:
                continue

    def _transform_event_to_payload(self, event: Event) -> dict[str, Any]:
        """
        Transform an SDK Event to the API's TelemetryPayload format.

        API expects:
        {
            "source": "backend-fastapi",
            "type": "error",
            "severity": "high",
            "environment": "production",
            "payload": { ... event data ... },
            "timestamp": "...",
            "trace_id": "..."
        }
        """
        # Map SDK level to API type/severity
        level = event.get("level", "info")
        event_type = "error" if level in ("error", "warning") else "info"
        severity_map = {
            "error": "high",
            "warning": "medium",
            "info": "low",
            "debug": "info",
        }
        severity = severity_map.get(level, "medium")

        # Build payload with exception details
        payload: dict[str, Any] = {
            "message": event.get("message"),
        }

        exception = event.get("exception")
        if exception:
            payload["error_type"] = exception.get("type")
            payload["error_message"] = exception.get("value")

            # Extract file and line from stack trace
            stacktrace = exception.get("stacktrace", [])
            if stacktrace:
                # Use the last frame (where the error occurred)
                last_frame = stacktrace[-1]
                payload["file"] = last_frame.get("filename")
                payload["line"] = last_frame.get("lineno")

                # Build full stack trace string
                trace_lines = []
                for frame in stacktrace:
                    line = f"  File \"{frame.get('filename')}\", line {frame.get('lineno')}, in {frame.get('function')}"
                    trace_lines.append(line)
                    if frame.get("context_line"):
                        trace_lines.append(f"    {frame.get('context_line')}")
                payload["stack_trace"] = "\n".join(trace_lines)

        # Add context data
        context = event.get("context", {})
        if context:
            payload["context"] = context

        # Add tags and extra data
        if event.get("tags"):
            payload["tags"] = event["tags"]
        if event.get("extra"):
            payload["extra"] = event["extra"]

        return {
            "source": "sdk-python",
            "type": event_type,
            "severity": severity,
            "environment": event.get("environment", "production"),
            "payload": payload,
            "timestamp": event.get("timestamp"),
            "trace_id": event.get("event_id"),  # Use event_id as trace_id for correlation
        }

    def _send_event(self, event: Event) -> None:
        """Send a single event with retry logic."""
        payload = self._transform_event_to_payload(event)
        endpoint = f"{self._base_url}/v1/telemetry"

        headers = {
            "Content-Type": "application/json",
        }

        # Add API key authorization if present
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        for attempt in range(self._max_retries):
            try:
                response = self._client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                if self._debug:
                    logger.debug(f"Sent event {event.get('event_id')} successfully")
                return
            except httpx.HTTPStatusError as e:
                if e.response.status_code < 500:
                    # Client error, don't retry
                    logger.error(f"Failed to send event: {e.response.status_code} - {e.response.text}")
                    return
                # Server error, retry
                if self._debug:
                    logger.warning(f"Server error (attempt {attempt + 1}): {e}")
            except httpx.RequestError as e:
                if self._debug:
                    logger.warning(f"Request error (attempt {attempt + 1}): {e}")

        logger.error(f"Failed to send event {event.get('event_id')} after {self._max_retries} attempts")
