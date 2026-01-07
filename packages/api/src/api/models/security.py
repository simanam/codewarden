"""CodeWarden Security Models - Models for security scanning."""

from typing import Any

from pydantic import BaseModel, Field


class SecurityFinding(BaseModel):
    """A single security finding from a scan."""

    id: str
    type: str  # 'dependency', 'secret', 'code'
    severity: str  # 'critical', 'high', 'medium', 'low'
    title: str
    description: str | None = None
    file_path: str | None = None
    line_number: int | None = None
    column_number: int | None = None
    cwe_id: str | None = None
    cve_id: str | None = None
    package_name: str | None = None
    package_version: str | None = None
    fixed_version: str | None = None
    remediation: str | None = None
    raw_data: dict[str, Any] | None = None


class ScanTriggerRequest(BaseModel):
    """Request to trigger a security scan."""

    scan_type: str = Field(
        default="full",
        description="Type of scan: 'full', 'dependencies', 'secrets', 'code'",
    )


class ScanResponse(BaseModel):
    """Response for a security scan."""

    id: str
    app_id: str
    scan_type: str
    status: str  # 'running', 'passed', 'failed', 'error'
    started_at: str
    completed_at: str | None = None
    duration_ms: int | None = None
    vulnerability_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0


class ScanDetailResponse(ScanResponse):
    """Detailed scan response with findings."""

    findings: list[SecurityFinding] = []
    fix_commands: list[str] = []


class ScanListResponse(BaseModel):
    """List of scans."""

    scans: list[ScanResponse]
    total: int


class SecuritySummary(BaseModel):
    """Security summary for an app."""

    last_scan_at: str | None = None
    last_scan_status: str | None = None
    total_vulnerabilities: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    by_type: dict[str, int] = {}
    trend: str = "stable"  # 'improving', 'stable', 'degrading'


class SecurityConfig(BaseModel):
    """Security configuration for an app."""

    scan_on_startup: bool = True
    scan_schedule: str | None = None  # cron expression
    notify_on_critical: bool = True
    notify_on_high: bool = True
    auto_create_issues: bool = False
    excluded_paths: list[str] = []
    excluded_rules: list[str] = []
