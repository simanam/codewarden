"""Evidence Collector for SOC 2 compliance.

Aggregates and sends evidence events to the CodeWarden API for compliance
reporting and audit trails.
"""

import os
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from codewarden.client import CodeWardenClient


class EvidenceType(str, Enum):
    """Types of evidence events."""

    DEPLOYMENT = "AUDIT_DEPLOY"
    SCAN = "AUDIT_SCAN"
    ACCESS = "AUDIT_ACCESS"
    CONFIG_CHANGE = "AUDIT_CONFIG"
    EXPORT = "AUDIT_EXPORT"
    INCIDENT = "AUDIT_INCIDENT"


@dataclass
class EvidenceEvent:
    """A single evidence event for compliance logging."""

    event_type: EvidenceType
    title: str
    description: Optional[str] = None
    severity: str = "info"  # 'info', 'warning', 'critical'
    actor: Optional[str] = None  # User or system that triggered
    ip_address: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class EvidenceCollector:
    """Collect and send compliance evidence to CodeWarden.

    The EvidenceCollector provides a unified interface for logging various
    types of compliance events required for SOC 2 and other security audits.

    Example:
        >>> from codewarden.evidence import EvidenceCollector
        >>> collector = EvidenceCollector(client)
        >>>
        >>> # Log a deployment
        >>> collector.log_deployment(
        ...     version="1.2.3",
        ...     commit_sha="abc123",
        ...     deployer="ci-bot",
        ...     environment="production"
        ... )
        >>>
        >>> # Log a security scan
        >>> collector.log_scan_result(
        ...     scan_type="dependency",
        ...     findings_count=3,
        ...     critical_count=0
        ... )
    """

    def __init__(
        self,
        client: Optional[CodeWardenClient] = None,
        auto_detect_context: bool = True,
    ):
        """Initialize evidence collector.

        Args:
            client: CodeWarden client instance. If None, uses global client.
            auto_detect_context: Automatically detect hostname, IP, etc.
        """
        self._client = client
        self._auto_detect = auto_detect_context
        self._hostname: Optional[str] = None
        self._ip_address: Optional[str] = None

        if auto_detect_context:
            self._detect_context()

    def _detect_context(self) -> None:
        """Auto-detect execution context."""
        try:
            self._hostname = socket.gethostname()
            self._ip_address = socket.gethostbyname(self._hostname)
        except Exception:
            pass

    def _get_client(self) -> CodeWardenClient:
        """Get the CodeWarden client instance."""
        if self._client:
            return self._client

        import codewarden

        return codewarden.get_client()

    def _send_evidence(self, event: EvidenceEvent) -> Optional[str]:
        """Send evidence event to API.

        Args:
            event: Evidence event to send

        Returns:
            Event ID if successful, None otherwise
        """
        try:
            client = self._get_client()

            payload = {
                "event_type": event.event_type.value,
                "data": {
                    "title": event.title,
                    "description": event.description,
                    "severity": event.severity,
                    "timestamp": event.timestamp,
                    **event.metadata,
                },
                "actor": event.actor,
                "ip_address": event.ip_address or self._ip_address,
                "hostname": self._hostname,
            }

            # Use the evidence endpoint
            response = client._http_client.post(
                f"{client._ingest_url}/v1/evidence",
                json=payload,
                headers={"Authorization": f"Bearer {client._api_key}"},
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("event_id")

        except Exception as e:
            if self._client and self._client._debug:
                print(f"[CodeWarden] Evidence send error: {e}")

        return None

    def log_event(self, event: EvidenceEvent) -> Optional[str]:
        """Log a generic evidence event.

        Args:
            event: Evidence event to log

        Returns:
            Event ID if successful
        """
        return self._send_evidence(event)

    def log_deployment(
        self,
        version: str,
        commit_sha: Optional[str] = None,
        deployer: Optional[str] = None,
        environment: str = "production",
        branch: Optional[str] = None,
        build_url: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Log a deployment event.

        Args:
            version: Version being deployed
            commit_sha: Git commit SHA
            deployer: User or service performing deploy
            environment: Target environment
            branch: Git branch name
            build_url: URL to CI/CD build
            metadata: Additional metadata

        Returns:
            Event ID if successful

        Example:
            >>> collector.log_deployment(
            ...     version="2.1.0",
            ...     commit_sha="abc123def",
            ...     deployer="github-actions",
            ...     environment="production",
            ...     branch="main"
            ... )
        """
        event = EvidenceEvent(
            event_type=EvidenceType.DEPLOYMENT,
            title=f"Deployment: {version} to {environment}",
            description=f"Version {version} deployed to {environment}",
            severity="info",
            actor=deployer or self._detect_deployer(),
            metadata={
                "version": version,
                "commit_sha": commit_sha,
                "environment": environment,
                "branch": branch,
                "build_url": build_url,
                **(metadata or {}),
            },
        )

        return self._send_evidence(event)

    def log_scan_result(
        self,
        scan_type: str,
        status: str = "completed",
        findings_count: int = 0,
        critical_count: int = 0,
        high_count: int = 0,
        medium_count: int = 0,
        low_count: int = 0,
        scan_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        duration_ms: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Log a security scan result.

        Args:
            scan_type: Type of scan (dependency, secret, code, full)
            status: Scan status (running, passed, failed, error)
            findings_count: Total number of findings
            critical_count: Number of critical findings
            high_count: Number of high severity findings
            medium_count: Number of medium severity findings
            low_count: Number of low severity findings
            scan_id: Unique scan identifier
            tool_name: Tool used for scanning
            duration_ms: Scan duration in milliseconds
            metadata: Additional metadata

        Returns:
            Event ID if successful

        Example:
            >>> collector.log_scan_result(
            ...     scan_type="dependency",
            ...     status="failed",
            ...     findings_count=5,
            ...     critical_count=1,
            ...     tool_name="pip-audit"
            ... )
        """
        severity = "info"
        if critical_count > 0:
            severity = "critical"
        elif high_count > 0:
            severity = "warning"

        event = EvidenceEvent(
            event_type=EvidenceType.SCAN,
            title=f"Security Scan: {scan_type} - {status}",
            description=f"{scan_type.title()} scan completed with {findings_count} findings",
            severity=severity,
            actor=tool_name or "codewarden",
            metadata={
                "scan_type": scan_type,
                "status": status,
                "findings_count": findings_count,
                "severity_breakdown": {
                    "critical": critical_count,
                    "high": high_count,
                    "medium": medium_count,
                    "low": low_count,
                },
                "scan_id": scan_id,
                "tool_name": tool_name,
                "duration_ms": duration_ms,
                **(metadata or {}),
            },
        )

        return self._send_evidence(event)

    def log_access(
        self,
        action: str,
        resource: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Log an access/authentication event.

        Args:
            action: Action performed (login, logout, api_access, etc.)
            resource: Resource being accessed
            user_id: User identifier
            user_email: User email
            success: Whether access was successful
            ip_address: Client IP address
            user_agent: Client user agent
            metadata: Additional metadata

        Returns:
            Event ID if successful

        Example:
            >>> collector.log_access(
            ...     action="login",
            ...     resource="dashboard",
            ...     user_email="user@example.com",
            ...     success=True,
            ...     ip_address="192.168.1.1"
            ... )
        """
        event = EvidenceEvent(
            event_type=EvidenceType.ACCESS,
            title=f"Access: {action} on {resource}",
            description=f"{'Successful' if success else 'Failed'} {action} on {resource}",
            severity="info" if success else "warning",
            actor=user_email or user_id,
            ip_address=ip_address,
            metadata={
                "action": action,
                "resource": resource,
                "user_id": user_id,
                "user_email": user_email,
                "success": success,
                "user_agent": user_agent,
                **(metadata or {}),
            },
        )

        return self._send_evidence(event)

    def log_config_change(
        self,
        setting_name: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        changed_by: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Log a configuration change.

        Args:
            setting_name: Name of the setting changed
            old_value: Previous value (redacted if sensitive)
            new_value: New value (redacted if sensitive)
            changed_by: User who made the change
            reason: Reason for the change
            metadata: Additional metadata

        Returns:
            Event ID if successful

        Example:
            >>> collector.log_config_change(
            ...     setting_name="max_retries",
            ...     old_value="3",
            ...     new_value="5",
            ...     changed_by="admin@example.com"
            ... )
        """
        event = EvidenceEvent(
            event_type=EvidenceType.CONFIG_CHANGE,
            title=f"Config Change: {setting_name}",
            description=f"Configuration '{setting_name}' changed",
            severity="info",
            actor=changed_by,
            metadata={
                "setting_name": setting_name,
                "old_value": self._redact_if_sensitive(setting_name, old_value),
                "new_value": self._redact_if_sensitive(setting_name, new_value),
                "reason": reason,
                **(metadata or {}),
            },
        )

        return self._send_evidence(event)

    def log_incident(
        self,
        title: str,
        description: str,
        severity: str = "warning",
        incident_type: Optional[str] = None,
        affected_systems: Optional[list[str]] = None,
        reporter: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Log a security incident.

        Args:
            title: Incident title
            description: Detailed description
            severity: Severity level (info, warning, critical)
            incident_type: Type of incident
            affected_systems: List of affected systems
            reporter: Who reported the incident
            metadata: Additional metadata

        Returns:
            Event ID if successful

        Example:
            >>> collector.log_incident(
            ...     title="Unusual login activity detected",
            ...     description="Multiple failed login attempts from same IP",
            ...     severity="warning",
            ...     incident_type="brute_force_attempt"
            ... )
        """
        event = EvidenceEvent(
            event_type=EvidenceType.INCIDENT,
            title=f"Incident: {title}",
            description=description,
            severity=severity,
            actor=reporter or "system",
            metadata={
                "incident_type": incident_type,
                "affected_systems": affected_systems,
                "reporter": reporter,
                **(metadata or {}),
            },
        )

        return self._send_evidence(event)

    def _detect_deployer(self) -> Optional[str]:
        """Try to detect who is deploying from environment."""
        # Check common CI/CD environment variables
        ci_vars = [
            "GITHUB_ACTOR",
            "GITLAB_USER_LOGIN",
            "CIRCLE_USERNAME",
            "BITBUCKET_STEP_TRIGGERER_UUID",
            "TRAVIS_COMMIT_AUTHOR",
            "USER",
        ]

        for var in ci_vars:
            value = os.environ.get(var)
            if value:
                return value

        return None

    def _redact_if_sensitive(
        self,
        setting_name: str,
        value: Optional[str],
    ) -> Optional[str]:
        """Redact value if setting name indicates sensitivity."""
        if not value:
            return value

        sensitive_patterns = [
            "password",
            "secret",
            "key",
            "token",
            "credential",
            "api_key",
            "auth",
        ]

        name_lower = setting_name.lower()
        for pattern in sensitive_patterns:
            if pattern in name_lower:
                return "[REDACTED]"

        return value


# Singleton instance for convenience
_collector: Optional[EvidenceCollector] = None


def get_collector() -> EvidenceCollector:
    """Get the global evidence collector instance."""
    global _collector
    if _collector is None:
        _collector = EvidenceCollector()
    return _collector


def log_deployment(**kwargs) -> Optional[str]:
    """Convenience function to log a deployment."""
    return get_collector().log_deployment(**kwargs)


def log_scan_result(**kwargs) -> Optional[str]:
    """Convenience function to log a scan result."""
    return get_collector().log_scan_result(**kwargs)


def log_access(**kwargs) -> Optional[str]:
    """Convenience function to log an access event."""
    return get_collector().log_access(**kwargs)


def log_config_change(**kwargs) -> Optional[str]:
    """Convenience function to log a config change."""
    return get_collector().log_config_change(**kwargs)


def log_incident(**kwargs) -> Optional[str]:
    """Convenience function to log an incident."""
    return get_collector().log_incident(**kwargs)
