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

    def send_scan_results(
        self,
        scan_result: Any,
        scan_type: str = "full",
    ) -> str:
        """Send security scan results to CodeWarden.

        Args:
            scan_result: ScanResult from run_security_scan()
            scan_type: Type of scan performed

        Returns:
            Evidence event ID
        """
        # Build findings list for the API
        findings = []
        for finding in scan_result.findings:
            findings.append({
                "type": finding.type,
                "severity": finding.severity,
                "title": finding.title,
                "description": finding.description,
                "file_path": finding.file_path,
                "line_number": finding.line_number,
                "cwe_id": finding.cwe_id,
                "cve_id": finding.cve_id,
                "package_name": finding.package_name,
                "package_version": finding.package_version,
                "fixed_version": finding.fixed_version,
                "remediation": finding.remediation,
            })

        # Send as evidence event
        evidence_data = {
            "scan_type": scan_type,
            "total_findings": scan_result.total_count,
            "severity_breakdown": scan_result.severity_counts,
            "findings": findings,
            "errors": scan_result.errors,
        }

        return self._transport.send_evidence("AUDIT_SCAN", evidence_data)

    def run_security_scan(
        self,
        target_path: str = ".",
        scan_type: str = "full",
        send_results: bool = True,
    ) -> Any:
        """Run security scan and optionally send results to CodeWarden.

        Args:
            target_path: Directory to scan
            scan_type: Type of scan ('full', 'dependencies', 'secrets', 'code')
            send_results: Whether to send results to CodeWarden API

        Returns:
            ScanResult with all findings

        Example:
            >>> client = codewarden.get_client()
            >>> result = client.run_security_scan("./src")
            >>> print(f"Found {result.total_count} issues")
        """
        from codewarden.scanners import run_security_scan

        result = run_security_scan(
            target_path=target_path,
            scan_dependencies=scan_type in ("full", "dependencies"),
            scan_secrets=scan_type in ("full", "secrets"),
            scan_code=scan_type in ("full", "code"),
        )

        if send_results:
            self.send_scan_results(result, scan_type)

        return result

    def flush(self) -> None:
        """Flush all pending events."""
        self._transport.flush()

    def close(self) -> None:
        """Close the client and flush pending events."""
        self.flush()
        self._transport.close()
