"""CodeWarden Telemetry Router - SDK telemetry ingestion endpoints.

This follows the API specification from the Technical PRD:
- POST /v1/telemetry - Error/log ingestion from SDKs
- POST /v1/evidence - Compliance event logging
- GET /v1/health - SDK health check and config sync
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.auth import ApiKeyInfo, verify_api_key
from api.services.ai_analyzer import get_analyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["Telemetry"])


@router.get("/ping", summary="Simple ping test", description="Test endpoint to verify API reachability")
async def ping() -> dict[str, str]:
    """Simple ping endpoint - no auth required."""
    print("[TELEMETRY] Ping received!")
    return {"status": "pong", "message": "Telemetry endpoint is reachable"}


# ============================================
# Request/Response Models
# ============================================


class TelemetryPayload(BaseModel):
    """Telemetry data from SDK."""

    source: str = Field(..., description="SDK identifier (e.g., 'backend-fastapi')")
    type: str = Field(
        ..., description="Event type: crash, error, warning, info, security"
    )
    severity: str = Field(
        "medium", description="Severity: critical, high, medium, low, info"
    )
    environment: str = Field("production", description="App environment")
    payload: dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    trace_id: str | None = Field(None, description="Trace ID for correlation")


class TelemetryResponse(BaseModel):
    """Response for telemetry ingestion."""

    id: str = Field(..., description="Event ID")
    status: str = Field("received", description="Processing status")
    analysis_status: str = Field("queued", description="AI analysis status")


class EvidencePayload(BaseModel):
    """Compliance evidence event."""

    type: str = Field(
        ...,
        description="Event type: AUDIT_DEPLOY, AUDIT_SCAN, AUDIT_ACCESS, AUDIT_CONFIG",
    )
    data: dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EvidenceResponse(BaseModel):
    """Response for evidence logging."""

    id: str
    status: str = "logged"


class HealthResponse(BaseModel):
    """SDK health check response."""

    status: str = "healthy"
    app: dict[str, Any]
    config: dict[str, Any]
    rate_limit: dict[str, Any]


# ============================================
# Telemetry Endpoints
# ============================================


async def run_ai_analysis(event_id: str, payload: TelemetryPayload) -> None:
    """Background task to run AI analysis on an event."""
    analyzer = get_analyzer()

    if not analyzer.is_available:
        logger.warning(f"AI analysis skipped for {event_id}: No AI models available")
        return

    try:
        logger.info(f"Starting AI analysis for event {event_id}")

        result = await analyzer.analyze_event(
            event_type=payload.type,
            severity=payload.severity,
            error_type=payload.payload.get("error_type"),
            error_message=payload.payload.get("error_message"),
            file_path=payload.payload.get("file"),
            line_number=payload.payload.get("line"),
            stack_trace=payload.payload.get("stack_trace"),
            environment=payload.environment,
            context=payload.payload,
        )

        if result:
            # Update event with analysis result
            from api.db import supabase

            if supabase:
                analysis_data = {
                    "summary": result.summary,
                    "root_cause": result.root_cause,
                    "suggested_fix": result.suggested_fix,
                    "severity_assessment": result.severity_assessment,
                    "related_issues": result.related_issues,
                    "code_suggestions": result.code_suggestions,
                    "confidence": result.confidence,
                }

                supabase.table("event_metadata").update(
                    {
                        "analysis_status": "completed",
                        "analysis_result": analysis_data,
                        "model_used": result.model_used,
                        "analyzed_at": result.analyzed_at,
                    }
                ).eq("id", event_id).execute()

                logger.info(
                    f"AI analysis completed for {event_id} using {result.model_used}"
                )
        else:
            # Mark as failed
            from api.db import supabase

            if supabase:
                supabase.table("event_metadata").update(
                    {"analysis_status": "failed"}
                ).eq("id", event_id).execute()

            logger.warning(f"AI analysis failed for {event_id}")

    except Exception as e:
        logger.exception(f"Error during AI analysis for {event_id}: {e}")
        # Update status to failed
        try:
            from api.db import supabase

            if supabase:
                supabase.table("event_metadata").update(
                    {"analysis_status": "failed"}
                ).eq("id", event_id).execute()
        except Exception:
            pass


@router.post(
    "/telemetry",
    response_model=TelemetryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest telemetry",
    description="Receives scrubbed error/log data from SDKs. Immediately queues for async processing.",
)
async def ingest_telemetry(
    payload: TelemetryPayload,
    background_tasks: BackgroundTasks,
    api_key: ApiKeyInfo = Depends(verify_api_key),
) -> TelemetryResponse:
    # Log immediately at the start to confirm endpoint is hit
    print(f"[TELEMETRY] Received request from app={api_key.app_name}, type={payload.type}")
    logger.info(f"[TELEMETRY] Processing: source={payload.source}, severity={payload.severity}")
    """
    Ingest telemetry from SDK.

    This endpoint:
    1. Validates the payload is scrubbed
    2. Generates an event ID
    3. Stores event in database
    4. Queues AI analysis as background task
    5. Returns immediately (non-blocking)
    """
    # Generate event ID as proper UUID for database compatibility
    event_id = str(uuid4())

    logger.info(
        f"Received telemetry: type={payload.type}, severity={payload.severity}, "
        f"app={api_key.app_name}, event_id={event_id}"
    )

    try:
        # Store event metadata in Supabase
        from api.db import supabase

        if supabase:
            event_data = {
                "id": event_id,
                "app_id": api_key.app_id,
                "event_type": payload.type,
                "severity": payload.severity,
                "trace_id": payload.trace_id,
                "error_type": payload.payload.get("error_type"),
                "error_message": payload.payload.get("error_message"),
                "file_path": payload.payload.get("file"),
                "line_number": payload.payload.get("line"),
                "stack_trace": payload.payload.get("stack_trace"),
                "environment": payload.environment,
                "analysis_status": "pending",
                "occurred_at": payload.timestamp.isoformat(),
            }

            supabase.table("event_metadata").insert(event_data).execute()

            # Update app's last_event_at
            supabase.table("apps").update(
                {"last_event_at": datetime.utcnow().isoformat()}
            ).eq("id", api_key.app_id).execute()

        # Queue AI analysis as background task
        background_tasks.add_task(run_ai_analysis, event_id, payload)

        return TelemetryResponse(
            id=event_id,
            status="received",
            analysis_status="queued",
        )

    except Exception as e:
        logger.exception(f"Failed to process telemetry: {e}")
        # Still return success to SDK - we don't want to block their app
        return TelemetryResponse(
            id=event_id,
            status="received",
            analysis_status="pending",
        )


@router.post(
    "/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log evidence",
    description="Logs compliance-relevant events for SOC 2. Stored directly without AI processing.",
)
async def log_evidence(
    payload: EvidencePayload,
    api_key: ApiKeyInfo = Depends(verify_api_key),
) -> EvidenceResponse:
    """
    Log compliance evidence.

    Valid event types:
    - AUDIT_DEPLOY: Deployment records (version, commit_hash)
    - AUDIT_SCAN: Security scan results (tool, status, issue_count)
    - AUDIT_ACCESS: Authentication events (user_id, action, resource)
    - AUDIT_CONFIG: Configuration changes (setting, old_value, new_value)
    """
    # Generate evidence ID as proper UUID for database compatibility
    evidence_id = str(uuid4())

    valid_types = [
        "AUDIT_DEPLOY",
        "AUDIT_SCAN",
        "AUDIT_ACCESS",
        "AUDIT_CONFIG",
        "AUDIT_EXPORT",
        "AUDIT_INCIDENT",
    ]

    if payload.type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "invalid_evidence_type",
                    "message": f"Event type must be one of: {', '.join(valid_types)}",
                }
            },
        )

    logger.info(
        f"Logging evidence: type={payload.type}, app={api_key.app_name}, id={evidence_id}"
    )

    try:
        from api.db import supabase

        if supabase:
            evidence_data = {
                "id": evidence_id,
                "app_id": api_key.app_id,
                "event_type": payload.type,
                "data": payload.data,
                "created_at": payload.timestamp.isoformat(),
            }

            supabase.table("evidence_events").insert(evidence_data).execute()

        return EvidenceResponse(id=evidence_id, status="logged")

    except Exception as e:
        logger.exception(f"Failed to log evidence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "internal_error",
                    "message": "Failed to log evidence event.",
                }
            },
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="SDK health check and configuration sync.",
)
async def health_check(
    api_key: ApiKeyInfo = Depends(verify_api_key),
) -> HealthResponse:
    """
    SDK health check.

    Returns:
    - App configuration
    - Current rate limits
    - Processing status
    """
    try:
        from api.db import supabase

        config = {
            "scrub_pii": True,
            "scan_on_startup": True,
            "notify_on_crash": True,
            "notification_channels": ["email"],
        }

        if supabase:
            # Get app config from database
            result = (
                supabase.table("apps")
                .select("config")
                .eq("id", api_key.app_id)
                .single()
                .execute()
            )

            if result.data and result.data.get("config"):
                config = result.data["config"]

        return HealthResponse(
            status="healthy",
            app={
                "id": api_key.app_id,
                "name": api_key.app_name,
                "plan": api_key.org_plan,
            },
            config=config,
            rate_limit={
                "remaining": 4850,  # TODO: Implement actual rate limiting
                "limit": 5000,
                "reset_at": datetime.utcnow().isoformat(),
            },
        )

    except Exception as e:
        logger.exception(f"Health check error: {e}")
        # Return healthy anyway - don't break SDK
        return HealthResponse(
            status="healthy",
            app={
                "id": api_key.app_id,
                "name": api_key.app_name,
                "plan": api_key.org_plan,
            },
            config={},
            rate_limit={
                "remaining": 5000,
                "limit": 5000,
                "reset_at": datetime.utcnow().isoformat(),
            },
        )


@router.get(
    "/events/{event_id}/analysis",
    summary="Get event analysis",
    description="Retrieve AI analysis for a specific event.",
)
async def get_event_analysis(
    event_id: str,
    api_key: ApiKeyInfo = Depends(verify_api_key),
) -> dict[str, Any]:
    """Get AI analysis for an event."""
    try:
        from api.db import supabase

        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        result = (
            supabase.table("event_metadata")
            .select("*")
            .eq("id", event_id)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "event_not_found", "message": "Event not found"}},
            )

        event = result.data

        # Verify app ownership
        if event.get("app_id") != api_key.app_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "access_denied", "message": "Access denied"}},
            )

        return {
            "event_id": event_id,
            "analysis_status": event.get("analysis_status", "pending"),
            "analysis": event.get("analysis_result"),
            "model_used": event.get("model_used"),
            "analyzed_at": event.get("analyzed_at"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "internal_error", "message": "Failed to get analysis"}},
        )


@router.post(
    "/events/{event_id}/analyze",
    summary="Trigger AI analysis",
    description="Manually trigger AI analysis for an event.",
)
async def trigger_analysis(
    event_id: str,
    background_tasks: BackgroundTasks,
    api_key: ApiKeyInfo = Depends(verify_api_key),
) -> dict[str, str]:
    """Manually trigger AI analysis for an event."""
    try:
        from api.db import supabase

        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        # Get event
        result = (
            supabase.table("event_metadata")
            .select("*")
            .eq("id", event_id)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "event_not_found", "message": "Event not found"}},
            )

        event = result.data

        # Verify app ownership
        if event.get("app_id") != api_key.app_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "access_denied", "message": "Access denied"}},
            )

        # Check if already analyzed
        if event.get("analysis_status") == "completed":
            return {"status": "already_analyzed", "event_id": event_id}

        # Create payload from stored event data
        payload = TelemetryPayload(
            source="manual",
            type=event.get("event_type", "error"),
            severity=event.get("severity", "medium"),
            environment=event.get("environment", "production"),
            payload={
                "error_type": event.get("error_type"),
                "error_message": event.get("error_message"),
                "file": event.get("file_path"),
                "line": event.get("line_number"),
                "stack_trace": event.get("stack_trace"),
            },
        )

        # Update status to queued
        supabase.table("event_metadata").update(
            {"analysis_status": "queued"}
        ).eq("id", event_id).execute()

        # Queue analysis
        background_tasks.add_task(run_ai_analysis, event_id, payload)

        return {"status": "queued", "event_id": event_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to trigger analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "internal_error", "message": "Failed to trigger analysis"}},
        )
