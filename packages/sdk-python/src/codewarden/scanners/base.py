"""Base classes for security scanners."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ScanFinding:
    """A single security finding from a scanner."""

    type: str  # 'dependency', 'secret', 'code'
    severity: str  # 'critical', 'high', 'medium', 'low'
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    remediation: Optional[str] = None
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    fixed_version: Optional[str] = None
    confidence: str = "high"  # 'high', 'medium', 'low'
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    raw_data: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert finding to dictionary."""
        return {
            "type": self.type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "remediation": self.remediation,
            "cwe_id": self.cwe_id,
            "cve_id": self.cve_id,
            "package_name": self.package_name,
            "package_version": self.package_version,
            "fixed_version": self.fixed_version,
            "confidence": self.confidence,
            "detected_at": self.detected_at,
        }


@dataclass
class ScanResult:
    """Result of a security scan."""

    findings: list[ScanFinding]
    total_count: int
    severity_counts: dict[str, int]
    errors: list[str] = field(default_factory=list)
    scan_duration_ms: Optional[float] = None
    scanned_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        """Convert result to dictionary."""
        return {
            "findings": [f.to_dict() for f in self.findings],
            "total_count": self.total_count,
            "severity_counts": self.severity_counts,
            "errors": self.errors,
            "scan_duration_ms": self.scan_duration_ms,
            "scanned_at": self.scanned_at,
        }

    def has_critical(self) -> bool:
        """Check if any critical findings exist."""
        return self.severity_counts.get("critical", 0) > 0

    def has_high(self) -> bool:
        """Check if any high severity findings exist."""
        return self.severity_counts.get("high", 0) > 0

    def get_findings_by_severity(self, severity: str) -> list[ScanFinding]:
        """Get findings filtered by severity."""
        return [f for f in self.findings if f.severity == severity]

    def get_findings_by_type(self, finding_type: str) -> list[ScanFinding]:
        """Get findings filtered by type."""
        return [f for f in self.findings if f.type == finding_type]


class BaseScannerModule(ABC):
    """Abstract base class for security scanners."""

    # Severity mapping for different scanner outputs
    SEVERITY_MAP: dict[str, str] = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "info": "low",
        "warning": "medium",
        "error": "high",
    }

    def __init__(self, config: Optional[dict] = None):
        """Initialize scanner.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._findings: list[ScanFinding] = []
        self._errors: list[str] = []

    @abstractmethod
    def scan(self) -> ScanResult:
        """Run the security scan.

        Returns:
            ScanResult with findings
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the scanner tool is available.

        Returns:
            True if scanner can run
        """
        pass

    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity to standard values.

        Args:
            severity: Raw severity string

        Returns:
            Normalized severity ('critical', 'high', 'medium', 'low')
        """
        return self.SEVERITY_MAP.get(severity.lower(), "medium")

    def _create_finding(
        self,
        type: str,
        severity: str,
        title: str,
        description: str,
        **kwargs,
    ) -> ScanFinding:
        """Create a standardized finding.

        Args:
            type: Finding type
            severity: Severity level
            title: Short title
            description: Detailed description
            **kwargs: Additional finding fields

        Returns:
            ScanFinding instance
        """
        return ScanFinding(
            type=type,
            severity=self._normalize_severity(severity),
            title=title,
            description=description,
            **kwargs,
        )

    def _build_result(self, start_time: float) -> ScanResult:
        """Build scan result from collected findings.

        Args:
            start_time: Scan start time from time.time()

        Returns:
            ScanResult with all findings
        """
        import time

        duration_ms = (time.time() - start_time) * 1000

        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        for finding in self._findings:
            if finding.severity in severity_counts:
                severity_counts[finding.severity] += 1

        return ScanResult(
            findings=self._findings,
            total_count=len(self._findings),
            severity_counts=severity_counts,
            errors=self._errors,
            scan_duration_ms=duration_ms,
        )
