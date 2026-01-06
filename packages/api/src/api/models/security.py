"""CodeWarden Security Models - Models for security scanning."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class SecurityFinding(BaseModel):
    """A single security finding from a scan."""

    id: str
    type: str  # 'dependency', 'secret', 'code'
    severity: str  # 'critical', 'high', 'medium', 'low'
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    fixed_version: Optional[str] = None
    remediation: Optional[str] = None
    raw_data: Optional[dict[str, Any]] = None


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
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
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

    last_scan_at: Optional[str] = None
    last_scan_status: Optional[str] = None
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
    scan_schedule: Optional[str] = None  # cron expression
    notify_on_critical: bool = True
    notify_on_high: bool = True
    auto_create_issues: bool = False
    excluded_paths: list[str] = []
    excluded_rules: list[str] = []
