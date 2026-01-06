"""CodeWarden Security Router - Security scanning endpoints.

Provides endpoints for:
- Triggering security scans (dependencies, secrets, code)
- Viewing scan history and results
- Security configuration
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from api.models.security import (
    ScanDetailResponse,
    ScanListResponse,
    ScanResponse,
    ScanTriggerRequest,
    SecurityFinding,
    SecuritySummary,
)
from api.routers.dashboard import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Security"])


# ============================================
# Security Scan Endpoints
# ============================================


@router.post(
    "/apps/{app_id}/scans",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger security scan",
    description="Start a new security scan for the app.",
)
async def trigger_scan(
    app_id: str,
    request: ScanTriggerRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
) -> ScanResponse:
    """Trigger a security scan for the app.

    Scan types:
    - 'full': Run all scanners (dependency, secret, code)
    - 'dependencies': Only scan for vulnerable dependencies
    - 'secrets': Only scan for leaked secrets
    - 'code': Only run static code analysis
    """
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            raise HTTPException(status_code=404, detail="App not found")

        # Verify app ownership
        app_result = (
            supabase.table("apps")
            .select("id, name, org_id")
            .eq("id", app_id)
            .eq("org_id", user["org_id"])
            .single()
            .execute()
        )

        if not app_result.data:
            raise HTTPException(status_code=404, detail="App not found")

        # Create scan record
        scan_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        # Determine tool name based on scan type
        tool_map = {
            "full": "codewarden",
            "dependencies": "pip-audit",
            "secrets": "gitleaks",
            "code": "bandit",
        }

        scan_data = {
            "id": scan_id,
            "app_id": app_id,
            "scan_type": request.scan_type,
            "tool_name": tool_map.get(request.scan_type, "codewarden"),
            "status": "running",
            "started_at": now,
        }

        result = supabase.table("security_scans").insert(scan_data).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create scan",
            )

        # Run scan in background
        async def run_scan():
            try:
                await _execute_scan(scan_id, app_id, request.scan_type)
            except Exception as e:
                logger.exception(f"Scan failed: {e}")
                supabase.table("security_scans").update(
                    {
                        "status": "error",
                        "completed_at": datetime.utcnow().isoformat(),
                    }
                ).eq("id", scan_id).execute()

        background_tasks.add_task(run_scan)

        return ScanResponse(
            id=scan_id,
            app_id=app_id,
            scan_type=request.scan_type,
            status="running",
            started_at=now,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to trigger scan: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger scan")


async def _execute_scan(scan_id: str, app_id: str, scan_type: str) -> None:
    """Execute the security scan and update results.

    This runs the appropriate scanners based on scan_type and stores
    the findings in the database.
    """
    from api.db import supabase

    if not supabase:
        return

    start_time = datetime.utcnow()
    all_findings: list[dict] = []
    fix_commands: list[str] = []
    errors: list[str] = []

    # Determine which scanners to run
    run_dependency = scan_type in ("full", "dependencies")
    run_secret = scan_type in ("full", "secrets")
    run_code = scan_type in ("full", "code")

    # For now, we'll create mock findings
    # In production, this would call the actual scanners or trigger
    # scanning on the client side via SDK

    # TODO: Integrate with actual scanner execution
    # This could be done by:
    # 1. Triggering scan on connected SDK clients via WebSocket
    # 2. Running server-side scans on uploaded code
    # 3. Fetching scan results from external CI/CD integrations

    # For demonstration, we create sample findings
    if run_dependency:
        # Sample dependency findings
        all_findings.append({
            "type": "dependency",
            "severity": "high",
            "title": "Vulnerable dependency: requests < 2.31.0",
            "description": "CVE-2023-32681: Unintended leak of Proxy-Authorization header",
            "package_name": "requests",
            "package_version": "2.28.0",
            "fixed_version": "2.31.0",
            "cve_id": "CVE-2023-32681",
            "remediation": "Upgrade requests to version 2.31.0 or higher",
        })
        fix_commands.append("pip install --upgrade requests>=2.31.0")

    if run_secret:
        # Sample secret finding
        all_findings.append({
            "type": "secret",
            "severity": "critical",
            "title": "Hardcoded API key detected",
            "description": "AWS Access Key ID pattern found in source code",
            "file_path": "config/settings.py",
            "line_number": 42,
            "remediation": "Remove hardcoded key and use environment variables",
        })

    if run_code:
        # Sample code finding
        all_findings.append({
            "type": "code",
            "severity": "medium",
            "title": "B101: Use of assert detected",
            "description": "Assert statements can be disabled in production",
            "file_path": "src/auth.py",
            "line_number": 15,
            "cwe_id": "CWE-703",
            "remediation": "Replace assert with proper exception handling",
        })

    # Calculate counts
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for finding in all_findings:
        sev = finding.get("severity", "medium")
        if sev in severity_counts:
            severity_counts[sev] += 1

    # Determine status
    status = "passed"
    if severity_counts["critical"] > 0 or severity_counts["high"] > 0:
        status = "failed"
    elif len(all_findings) > 0:
        status = "passed"  # Has findings but none critical/high

    end_time = datetime.utcnow()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    # Add IDs to findings
    findings_with_ids = []
    for i, finding in enumerate(all_findings):
        finding["id"] = f"{scan_id}_{i}"
        findings_with_ids.append(finding)

    # Update scan record
    supabase.table("security_scans").update({
        "status": status,
        "vulnerability_count": len(all_findings),
        "critical_count": severity_counts["critical"],
        "high_count": severity_counts["high"],
        "medium_count": severity_counts["medium"],
        "low_count": severity_counts["low"],
        "findings": findings_with_ids,
        "fix_commands": fix_commands,
        "completed_at": end_time.isoformat(),
        "duration_ms": duration_ms,
    }).eq("id", scan_id).execute()

    # Log evidence event
    supabase.table("evidence_events").insert({
        "app_id": app_id,
        "event_type": "AUDIT_SCAN",
        "data": {
            "scan_id": scan_id,
            "scan_type": scan_type,
            "status": status,
            "findings_count": len(all_findings),
            "severity_breakdown": severity_counts,
            "duration_ms": duration_ms,
        },
    }).execute()

    logger.info(
        f"Scan {scan_id} completed: {status}, "
        f"{len(all_findings)} findings, {duration_ms}ms"
    )


@router.get(
    "/apps/{app_id}/scans",
    response_model=ScanListResponse,
    summary="List security scans",
    description="Get scan history for an app.",
)
async def list_scans(
    app_id: str,
    user: dict = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
) -> ScanListResponse:
    """List security scans for an app."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            return ScanListResponse(scans=[], total=0)

        # Verify app ownership
        app_result = (
            supabase.table("apps")
            .select("id")
            .eq("id", app_id)
            .eq("org_id", user["org_id"])
            .execute()
        )

        if not app_result.data:
            raise HTTPException(status_code=404, detail="App not found")

        # Get scans
        result = (
            supabase.table("security_scans")
            .select("*", count="exact")
            .eq("app_id", app_id)
            .order("started_at", desc=True)
            .limit(limit)
            .offset(offset)
            .execute()
        )

        scans = [
            ScanResponse(
                id=scan["id"],
                app_id=scan["app_id"],
                scan_type=scan["scan_type"],
                status=scan["status"],
                started_at=scan["started_at"],
                completed_at=scan.get("completed_at"),
                duration_ms=scan.get("duration_ms"),
                vulnerability_count=scan.get("vulnerability_count", 0),
                critical_count=scan.get("critical_count", 0),
                high_count=scan.get("high_count", 0),
                medium_count=scan.get("medium_count", 0),
                low_count=scan.get("low_count", 0),
            )
            for scan in result.data or []
        ]

        return ScanListResponse(scans=scans, total=result.count or 0)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list scans: {e}")
        return ScanListResponse(scans=[], total=0)


@router.get(
    "/scans/{scan_id}",
    response_model=ScanDetailResponse,
    summary="Get scan details",
    description="Get detailed scan results including findings.",
)
async def get_scan_details(
    scan_id: str,
    user: dict = Depends(get_current_user),
) -> ScanDetailResponse:
    """Get detailed scan results."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            raise HTTPException(status_code=404, detail="Scan not found")

        # Get scan with app ownership check
        result = (
            supabase.table("security_scans")
            .select("*, apps!inner(org_id)")
            .eq("id", scan_id)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Scan not found")

        scan = result.data

        # Verify org ownership
        if scan.get("apps", {}).get("org_id") != user["org_id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Parse findings
        findings = []
        raw_findings = scan.get("findings", [])
        if isinstance(raw_findings, list):
            for f in raw_findings:
                findings.append(
                    SecurityFinding(
                        id=f.get("id", ""),
                        type=f.get("type", "unknown"),
                        severity=f.get("severity", "medium"),
                        title=f.get("title", ""),
                        description=f.get("description"),
                        file_path=f.get("file_path"),
                        line_number=f.get("line_number"),
                        column_number=f.get("column_number"),
                        cwe_id=f.get("cwe_id"),
                        cve_id=f.get("cve_id"),
                        package_name=f.get("package_name"),
                        package_version=f.get("package_version"),
                        fixed_version=f.get("fixed_version"),
                        remediation=f.get("remediation"),
                        raw_data=f.get("raw_data"),
                    )
                )

        return ScanDetailResponse(
            id=scan["id"],
            app_id=scan["app_id"],
            scan_type=scan["scan_type"],
            status=scan["status"],
            started_at=scan["started_at"],
            completed_at=scan.get("completed_at"),
            duration_ms=scan.get("duration_ms"),
            vulnerability_count=scan.get("vulnerability_count", 0),
            critical_count=scan.get("critical_count", 0),
            high_count=scan.get("high_count", 0),
            medium_count=scan.get("medium_count", 0),
            low_count=scan.get("low_count", 0),
            findings=findings,
            fix_commands=scan.get("fix_commands", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get scan details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scan details")


@router.get(
    "/apps/{app_id}/security",
    response_model=SecuritySummary,
    summary="Get security summary",
    description="Get security summary for an app including trends.",
)
async def get_security_summary(
    app_id: str,
    user: dict = Depends(get_current_user),
) -> SecuritySummary:
    """Get security summary for an app."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            return SecuritySummary()

        # Verify app ownership
        app_result = (
            supabase.table("apps")
            .select("id")
            .eq("id", app_id)
            .eq("org_id", user["org_id"])
            .execute()
        )

        if not app_result.data:
            raise HTTPException(status_code=404, detail="App not found")

        # Get latest scan
        latest_scan = (
            supabase.table("security_scans")
            .select("*")
            .eq("app_id", app_id)
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )

        if not latest_scan.data:
            return SecuritySummary()

        scan = latest_scan.data[0]

        # Count findings by type
        by_type: dict[str, int] = {}
        findings = scan.get("findings", [])
        if isinstance(findings, list):
            for f in findings:
                ftype = f.get("type", "unknown")
                by_type[ftype] = by_type.get(ftype, 0) + 1

        # Calculate trend by comparing with previous scan
        previous_scan = (
            supabase.table("security_scans")
            .select("vulnerability_count")
            .eq("app_id", app_id)
            .order("started_at", desc=True)
            .offset(1)
            .limit(1)
            .execute()
        )

        trend = "stable"
        if previous_scan.data:
            prev_count = previous_scan.data[0].get("vulnerability_count", 0)
            curr_count = scan.get("vulnerability_count", 0)
            if curr_count < prev_count:
                trend = "improving"
            elif curr_count > prev_count:
                trend = "degrading"

        return SecuritySummary(
            last_scan_at=scan.get("completed_at") or scan.get("started_at"),
            last_scan_status=scan.get("status"),
            total_vulnerabilities=scan.get("vulnerability_count", 0),
            critical_count=scan.get("critical_count", 0),
            high_count=scan.get("high_count", 0),
            medium_count=scan.get("medium_count", 0),
            low_count=scan.get("low_count", 0),
            by_type=by_type,
            trend=trend,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get security summary: {e}")
        return SecuritySummary()


# ============================================
# Organization-wide Security Stats
# ============================================


class OrgSecurityStats(BaseModel):
    """Organization-wide security statistics."""

    total_apps: int = 0
    apps_scanned: int = 0
    total_vulnerabilities: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    last_scan_at: Optional[str] = None
    scans_this_week: int = 0


@router.get(
    "/security/stats",
    response_model=OrgSecurityStats,
    summary="Get organization security stats",
    description="Get security statistics across all apps.",
)
async def get_org_security_stats(
    user: dict = Depends(get_current_user),
) -> OrgSecurityStats:
    """Get organization-wide security statistics."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            return OrgSecurityStats()

        # Get all apps for org
        apps_result = (
            supabase.table("apps")
            .select("id")
            .eq("org_id", user["org_id"])
            .neq("status", "archived")
            .execute()
        )

        app_ids = [app["id"] for app in apps_result.data or []]
        total_apps = len(app_ids)

        if not app_ids:
            return OrgSecurityStats(total_apps=0)

        # Get latest scan for each app
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

        scans_result = (
            supabase.table("security_scans")
            .select("*")
            .in_("app_id", app_ids)
            .order("started_at", desc=True)
            .execute()
        )

        # Track unique apps with scans and aggregate stats
        apps_with_scans: set[str] = set()
        total_vuln = 0
        critical = 0
        high = 0
        medium = 0
        low = 0
        last_scan_at: Optional[str] = None
        scans_this_week = 0

        for scan in scans_result.data or []:
            app_id = scan.get("app_id")

            # Only count the latest scan per app for vulnerability totals
            if app_id not in apps_with_scans:
                apps_with_scans.add(app_id)
                total_vuln += scan.get("vulnerability_count", 0)
                critical += scan.get("critical_count", 0)
                high += scan.get("high_count", 0)
                medium += scan.get("medium_count", 0)
                low += scan.get("low_count", 0)

            # Track latest scan time
            scan_time = scan.get("completed_at") or scan.get("started_at")
            if not last_scan_at and scan_time:
                last_scan_at = scan_time

            # Count scans this week
            if scan_time and scan_time >= week_ago:
                scans_this_week += 1

        return OrgSecurityStats(
            total_apps=total_apps,
            apps_scanned=len(apps_with_scans),
            total_vulnerabilities=total_vuln,
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            last_scan_at=last_scan_at,
            scans_this_week=scans_this_week,
        )

    except Exception as e:
        logger.exception(f"Failed to get org security stats: {e}")
        return OrgSecurityStats()


# ============================================
# Evidence Endpoints
# ============================================


class EvidenceEventResponse(BaseModel):
    """Response for evidence events."""

    id: str
    event_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    severity: str = "info"
    actor_email: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: str


class EvidenceListResponse(BaseModel):
    """List of evidence events."""

    events: list[EvidenceEventResponse]
    total: int


class ExportRequest(BaseModel):
    """Request to export evidence."""

    format: str = "json"  # json, csv, pdf
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    event_types: Optional[list[str]] = None


class ExportResponse(BaseModel):
    """Response for export request."""

    id: str
    status: str  # pending, processing, completed, failed
    format: str
    download_url: Optional[str] = None
    record_count: Optional[int] = None
    error: Optional[str] = None


@router.get(
    "/apps/{app_id}/evidence",
    response_model=EvidenceListResponse,
    summary="List evidence events",
    description="Get evidence events for compliance reporting.",
)
async def list_evidence_events(
    app_id: str,
    user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    event_type: Optional[str] = None,
) -> EvidenceListResponse:
    """List evidence events for an app."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            return EvidenceListResponse(events=[], total=0)

        # Verify app ownership
        app_result = (
            supabase.table("apps")
            .select("id")
            .eq("id", app_id)
            .eq("org_id", user["org_id"])
            .execute()
        )

        if not app_result.data:
            raise HTTPException(status_code=404, detail="App not found")

        # Get evidence events
        query = (
            supabase.table("evidence_events")
            .select("*", count="exact")
            .eq("app_id", app_id)
            .order("created_at", desc=True)
            .limit(limit)
            .offset(offset)
        )

        if event_type:
            query = query.eq("event_type", event_type)

        result = query.execute()

        events = []
        for event in result.data or []:
            data = event.get("data", {})
            events.append(
                EvidenceEventResponse(
                    id=event["id"],
                    event_type=event["event_type"],
                    title=data.get("title"),
                    description=data.get("description"),
                    severity=data.get("severity", "info"),
                    actor_email=event.get("actor_email"),
                    ip_address=event.get("ip_address"),
                    created_at=event["created_at"],
                )
            )

        return EvidenceListResponse(events=events, total=result.count or 0)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list evidence: {e}")
        return EvidenceListResponse(events=[], total=0)


@router.post(
    "/apps/{app_id}/evidence/export",
    response_model=ExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Export evidence",
    description="Export evidence events in various formats.",
)
async def export_evidence(
    app_id: str,
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
) -> ExportResponse:
    """Export evidence events."""
    try:
        from api.db import supabase
        from api.services.evidence_exporter import ExportOptions, get_exporter

        if not supabase or not user.get("org_id"):
            raise HTTPException(status_code=404, detail="App not found")

        # Verify app ownership
        app_result = (
            supabase.table("apps")
            .select("id")
            .eq("id", app_id)
            .eq("org_id", user["org_id"])
            .execute()
        )

        if not app_result.data:
            raise HTTPException(status_code=404, detail="App not found")

        # Create export record
        export_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        export_data = {
            "id": export_id,
            "app_id": app_id,
            "org_id": user["org_id"],
            "format": request.format,
            "status": "pending",
            "filters": {
                "start_date": request.start_date,
                "end_date": request.end_date,
                "event_types": request.event_types,
            },
            "requested_at": now,
        }

        supabase.table("evidence_exports").insert(export_data).execute()

        # Process export in background
        async def process_export():
            try:
                exporter = get_exporter()

                # Parse dates
                start_date = None
                end_date = None
                if request.start_date:
                    start_date = datetime.fromisoformat(request.start_date.replace("Z", "+00:00"))
                if request.end_date:
                    end_date = datetime.fromisoformat(request.end_date.replace("Z", "+00:00"))

                options = ExportOptions(
                    format=request.format,
                    start_date=start_date,
                    end_date=end_date,
                    event_types=request.event_types,
                )

                result = await exporter.export(app_id, user["org_id"], options)

                if result.success:
                    # In production, upload to cloud storage and get URL
                    supabase.table("evidence_exports").update({
                        "status": "completed",
                        "record_count": result.record_count,
                        "completed_at": datetime.utcnow().isoformat(),
                    }).eq("id", export_id).execute()

                    logger.info(f"Export {export_id} completed: {result.record_count} records")
                else:
                    supabase.table("evidence_exports").update({
                        "status": "failed",
                        "completed_at": datetime.utcnow().isoformat(),
                    }).eq("id", export_id).execute()

            except Exception as e:
                logger.exception(f"Export {export_id} failed: {e}")
                supabase.table("evidence_exports").update({
                    "status": "failed",
                    "completed_at": datetime.utcnow().isoformat(),
                }).eq("id", export_id).execute()

        background_tasks.add_task(process_export)

        return ExportResponse(
            id=export_id,
            status="pending",
            format=request.format,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create export: {e}")
        raise HTTPException(status_code=500, detail="Failed to create export")


@router.get(
    "/exports/{export_id}",
    response_model=ExportResponse,
    summary="Get export status",
    description="Get the status of an evidence export.",
)
async def get_export_status(
    export_id: str,
    user: dict = Depends(get_current_user),
) -> ExportResponse:
    """Get export status."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            raise HTTPException(status_code=404, detail="Export not found")

        result = (
            supabase.table("evidence_exports")
            .select("*")
            .eq("id", export_id)
            .eq("org_id", user["org_id"])
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Export not found")

        export = result.data

        return ExportResponse(
            id=export["id"],
            status=export["status"],
            format=export["format"],
            download_url=export.get("file_url"),
            record_count=export.get("record_count"),
            error=export.get("error"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get export status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get export status")
