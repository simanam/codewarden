"""CodeWarden WatchDog - Enhanced error capture and context enrichment."""

from __future__ import annotations

import os
import platform
import sys
import threading
import traceback
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from codewarden.types import EventContext, ExceptionInfo, StackFrame


@dataclass
class Breadcrumb:
    """A breadcrumb records an event that happened before an error."""

    timestamp: str
    category: str
    message: str
    level: str = "info"
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemInfo:
    """System information captured at SDK initialization."""

    os_name: str
    os_version: str
    python_version: str
    python_implementation: str
    machine: str
    processor: str
    hostname: str

    @classmethod
    def capture(cls) -> "SystemInfo":
        """Capture current system information."""
        return cls(
            os_name=platform.system(),
            os_version=platform.release(),
            python_version=platform.python_version(),
            python_implementation=platform.python_implementation(),
            machine=platform.machine(),
            processor=platform.processor(),
            hostname=platform.node(),
        )

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return {
            "os.name": self.os_name,
            "os.version": self.os_version,
            "python.version": self.python_version,
            "python.implementation": self.python_implementation,
            "machine": self.machine,
            "processor": self.processor,
            "hostname": self.hostname,
        }


class WatchDog:
    """
    WatchDog monitors and enriches error capture with context.

    Features:
    - Breadcrumb tracking for recording events before errors
    - System information capture
    - Enhanced stack trace parsing with local variables
    - Thread-local context management
    - Exception handlers integration

    Example:
        >>> from codewarden.watchdog import WatchDog
        >>>
        >>> watchdog = WatchDog(max_breadcrumbs=50)
        >>> watchdog.add_breadcrumb("user", "User clicked submit button")
        >>>
        >>> try:
        ...     do_something()
        ... except Exception as e:
        ...     context = watchdog.enrich_exception(e)
    """

    def __init__(
        self,
        *,
        max_breadcrumbs: int = 100,
        capture_locals: bool = False,
        context_lines: int = 5,
    ) -> None:
        """
        Initialize WatchDog.

        Args:
            max_breadcrumbs: Maximum breadcrumbs to retain
            capture_locals: Capture local variables in stack traces (security risk)
            context_lines: Number of source context lines to capture
        """
        self._max_breadcrumbs = max_breadcrumbs
        self._capture_locals = capture_locals
        self._context_lines = context_lines

        # Thread-local storage for breadcrumbs
        self._local = threading.local()

        # System info captured once
        self._system_info = SystemInfo.capture()

        # Global exception handlers
        self._exception_handlers: list[Callable[[BaseException], None]] = []

    @property
    def _breadcrumbs(self) -> deque[Breadcrumb]:
        """Get thread-local breadcrumbs queue."""
        if not hasattr(self._local, "breadcrumbs"):
            self._local.breadcrumbs = deque(maxlen=self._max_breadcrumbs)
        return self._local.breadcrumbs

    def add_breadcrumb(
        self,
        category: str,
        message: str,
        level: str = "info",
        data: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a breadcrumb to track user/application activity.

        Args:
            category: Category of the breadcrumb (e.g., "ui", "http", "database")
            message: Human-readable message describing the event
            level: Log level (debug, info, warning, error)
            data: Additional structured data
        """
        breadcrumb = Breadcrumb(
            timestamp=datetime.now(timezone.utc).isoformat(),
            category=category,
            message=message,
            level=level,
            data=data or {},
        )
        self._breadcrumbs.append(breadcrumb)

    def clear_breadcrumbs(self) -> None:
        """Clear all breadcrumbs for the current thread."""
        self._breadcrumbs.clear()

    def get_breadcrumbs(self) -> list[dict[str, Any]]:
        """
        Get all breadcrumbs as a list of dictionaries.

        Returns:
            List of breadcrumb dictionaries
        """
        return [
            {
                "timestamp": b.timestamp,
                "category": b.category,
                "message": b.message,
                "level": b.level,
                "data": b.data,
            }
            for b in self._breadcrumbs
        ]

    def get_system_info(self) -> dict[str, str]:
        """Get captured system information."""
        return self._system_info.to_dict()

    def enrich_exception(
        self,
        exception: BaseException,
        context: EventContext | None = None,
    ) -> dict[str, Any]:
        """
        Enrich an exception with full context.

        Args:
            exception: The exception to enrich
            context: Additional context to include

        Returns:
            Dictionary with enriched exception data
        """
        enriched: dict[str, Any] = {
            "exception": self._parse_exception(exception),
            "breadcrumbs": self.get_breadcrumbs(),
            "system": self.get_system_info(),
            "runtime": self._get_runtime_info(),
        }

        if context:
            enriched["context"] = context

        return enriched

    def _parse_exception(self, exception: BaseException) -> ExceptionInfo:
        """
        Parse an exception with enhanced stack trace.

        Args:
            exception: The exception to parse

        Returns:
            Structured exception information
        """
        tb = traceback.extract_tb(exception.__traceback__)
        frames: list[StackFrame] = []

        for frame in tb:
            stack_frame: StackFrame = {
                "filename": frame.filename,
                "lineno": frame.lineno,
                "function": frame.name,
                "context_line": frame.line,
                "pre_context": [],
                "post_context": [],
            }

            # Try to capture source context
            if self._context_lines > 0:
                context = self._get_source_context(
                    frame.filename,
                    frame.lineno,
                    self._context_lines,
                )
                if context:
                    stack_frame["pre_context"] = context["pre"]
                    stack_frame["post_context"] = context["post"]

            frames.append(stack_frame)

        return {
            "type": type(exception).__name__,
            "value": str(exception),
            "module": type(exception).__module__,
            "stacktrace": frames,
        }

    def _get_source_context(
        self,
        filename: str,
        lineno: int,
        context_lines: int,
    ) -> dict[str, list[str]] | None:
        """
        Get source code context around a line.

        Args:
            filename: Source file path
            lineno: Line number (1-indexed)
            context_lines: Number of context lines

        Returns:
            Dictionary with pre and post context lines
        """
        try:
            with open(filename, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            # Convert to 0-indexed
            idx = lineno - 1

            # Get pre-context
            start = max(0, idx - context_lines)
            pre = [line.rstrip() for line in lines[start:idx]]

            # Get post-context
            end = min(len(lines), idx + context_lines + 1)
            post = [line.rstrip() for line in lines[idx + 1 : end]]

            return {"pre": pre, "post": post}
        except Exception:
            return None

    def _get_runtime_info(self) -> dict[str, Any]:
        """Get current runtime information."""
        return {
            "pid": os.getpid(),
            "thread_id": threading.current_thread().ident,
            "thread_name": threading.current_thread().name,
            "recursion_limit": sys.getrecursionlimit(),
            "executable": sys.executable,
        }

    def register_exception_handler(
        self,
        handler: Callable[[BaseException], None],
    ) -> None:
        """
        Register a global exception handler.

        Args:
            handler: Callable that receives exceptions
        """
        self._exception_handlers.append(handler)

    def handle_exception(self, exception: BaseException) -> None:
        """
        Pass an exception to all registered handlers.

        Args:
            exception: The exception to handle
        """
        for handler in self._exception_handlers:
            try:
                handler(exception)
            except Exception:
                # Don't let handler errors propagate
                pass

    def install_sys_hook(self) -> None:
        """
        Install a sys.excepthook to capture unhandled exceptions.

        Warning: This replaces the existing excepthook.
        """
        original_hook = sys.excepthook

        def watchdog_hook(
            exc_type: type[BaseException],
            exc_value: BaseException,
            exc_tb: Any,
        ) -> None:
            # Call our handlers first
            self.handle_exception(exc_value)
            # Then call the original hook
            original_hook(exc_type, exc_value, exc_tb)

        sys.excepthook = watchdog_hook


# Global WatchDog instance
_watchdog: WatchDog | None = None


def get_watchdog() -> WatchDog:
    """Get the global WatchDog instance."""
    global _watchdog
    if _watchdog is None:
        _watchdog = WatchDog()
    return _watchdog


def add_breadcrumb(
    category: str,
    message: str,
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> None:
    """Add a breadcrumb to the global WatchDog."""
    get_watchdog().add_breadcrumb(category, message, level, data)
