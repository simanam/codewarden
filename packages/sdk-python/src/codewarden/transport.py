"""CodeWarden Transport - HTTP transport layer."""

from __future__ import annotations

import atexit
import logging
import queue
import threading
from typing import Any

import httpx

from codewarden.exceptions import TransportError
from codewarden.types import Event

logger = logging.getLogger(__name__)


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
            dsn: Data Source Name for the ingest endpoint
            max_queue_size: Maximum events to queue
            batch_size: Events per batch
            flush_interval: Seconds between flushes
            timeout: HTTP timeout in seconds
            max_retries: Maximum retry attempts
            debug: Enable debug logging
        """
        self._dsn = dsn
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

        if events:
            self._send_batch(events)

    def close(self) -> None:
        """Close the transport and flush pending events."""
        self._shutdown.set()
        self.flush()
        self._client.close()

    def _worker_loop(self) -> None:
        """Background worker that batches and sends events."""
        while not self._shutdown.is_set():
            events: list[Event] = []

            # Collect batch
            try:
                # Wait for first event with timeout
                event = self._queue.get(timeout=self._flush_interval)
                events.append(event)

                # Collect more events if available
                while len(events) < self._batch_size:
                    try:
                        event = self._queue.get_nowait()
                        events.append(event)
                    except queue.Empty:
                        break
            except queue.Empty:
                continue

            if events:
                self._send_batch(events)

    def _send_batch(self, events: list[Event]) -> None:
        """Send a batch of events with retry logic."""
        for attempt in range(self._max_retries):
            try:
                response = self._client.post(
                    self._dsn,
                    json={"events": events},
                )
                response.raise_for_status()
                if self._debug:
                    logger.debug(f"Sent {len(events)} events successfully")
                return
            except httpx.HTTPStatusError as e:
                if e.response.status_code < 500:
                    # Client error, don't retry
                    logger.error(f"Failed to send events: {e}")
                    return
                # Server error, retry
                if self._debug:
                    logger.warning(f"Server error (attempt {attempt + 1}): {e}")
            except httpx.RequestError as e:
                if self._debug:
                    logger.warning(f"Request error (attempt {attempt + 1}): {e}")

        logger.error(f"Failed to send {len(events)} events after {self._max_retries} attempts")
