"""CodeWarden SDK Type Definitions."""

from __future__ import annotations

from typing import Literal, TypedDict


class EventContext(TypedDict, total=False):
    """Context information for an event."""

    user_id: str
    email: str
    username: str
    session_id: str
    request_id: str
    ip_address: str
    user_agent: str


class StackFrame(TypedDict):
    """A single stack frame in a traceback."""

    filename: str
    lineno: int
    function: str
    context_line: str | None
    pre_context: list[str]
    post_context: list[str]


class ExceptionInfo(TypedDict):
    """Structured exception information."""

    type: str
    value: str
    module: str | None
    stacktrace: list[StackFrame]


class Event(TypedDict, total=False):
    """A CodeWarden event."""

    event_id: str
    timestamp: str
    level: Literal["error", "warning", "info", "debug"]
    message: str
    exception: ExceptionInfo | None
    context: EventContext
    tags: dict[str, str]
    extra: dict[str, object]
    environment: str
    release: str | None
