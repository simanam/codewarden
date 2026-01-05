"""CodeWarden Event Models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class StackFrame(BaseModel):
    """A single stack frame in a traceback."""

    filename: str
    lineno: int
    function: str
    context_line: str | None = None
    pre_context: list[str] = Field(default_factory=list)
    post_context: list[str] = Field(default_factory=list)


class ExceptionInfo(BaseModel):
    """Structured exception information."""

    type: str
    value: str
    module: str | None = None
    stacktrace: list[StackFrame] = Field(default_factory=list)


class EventContext(BaseModel):
    """Context information for an event."""

    user_id: str | None = None
    email: str | None = None
    username: str | None = None
    session_id: str | None = None
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class Breadcrumb(BaseModel):
    """A breadcrumb record."""

    timestamp: str
    category: str
    message: str
    level: str = "info"
    data: dict[str, object] = Field(default_factory=dict)


class Event(BaseModel):
    """A CodeWarden event."""

    event_id: str
    timestamp: str
    level: Literal["error", "warning", "info", "debug"]
    message: str
    exception: ExceptionInfo | None = None
    context: EventContext = Field(default_factory=EventContext)
    tags: dict[str, str] = Field(default_factory=dict)
    extra: dict[str, object] = Field(default_factory=dict)
    breadcrumbs: list[Breadcrumb] = Field(default_factory=list)
    environment: str = "production"
    release: str | None = None
    project_id: str | None = None

    class Config:
        """Pydantic model config."""

        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:30:00Z",
                "level": "error",
                "message": "Connection timeout",
                "environment": "production",
                "context": {"user_id": "user_123", "request_id": "req_456"},
                "tags": {"service": "payment-api"},
            }
        }


class EventBatch(BaseModel):
    """A batch of events for ingestion."""

    events: list[Event]

    class Config:
        """Pydantic model config."""

        json_schema_extra = {
            "example": {
                "events": [
                    {
                        "event_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "level": "error",
                        "message": "Connection timeout",
                        "environment": "production",
                    }
                ]
            }
        }


class EventResponse(BaseModel):
    """Response after event ingestion."""

    success: bool
    event_ids: list[str]
    message: str = "Events received successfully"
