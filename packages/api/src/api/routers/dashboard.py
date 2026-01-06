"""CodeWarden Dashboard Router - Endpoints for the dashboard frontend.

These endpoints use Supabase JWT authentication (user sessions from dashboard).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header, Response, status
from pydantic import BaseModel, Field

from api.auth import generate_api_key, hash_api_key
from api.config import settings
from api.services.ai_analyzer import get_analyzer
from api.services.notifications import get_notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


# ============================================
# Authentication
# ============================================


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    """Verify Supabase JWT and return user info.

    The dashboard sends the Supabase access token which we verify
    using Supabase's auth API.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization token",
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    try:
        from api.db import supabase

        if not supabase:
            # Development mode - return mock user
            if settings.debug:
                return {
                    "id": "dev-user-id",
                    "email": "dev@codewarden.io",
                    "org_id": "dev-org-id",
                }
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not configured",
            )

        # Verify token with Supabase
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        user = user_response.user

        # Get user profile with org_id
        profile_result = (
            supabase.table("user_profiles")
            .select("org_id, role, display_name")
            .eq("id", user.id)
            .single()
            .execute()
        )

        org_id = None
        role = "member"
        display_name = None

        if profile_result.data:
            org_id = profile_result.data.get("org_id")
            role = profile_result.data.get("role", "member")
            display_name = profile_result.data.get("display_name")

        return {
            "id": user.id,
            "email": user.email,
            "org_id": org_id,
            "role": role,
            "display_name": display_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


# ============================================
# Models
# ============================================


class AppCreate(BaseModel):
    """Request to create a new app."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    environment: str = "production"
    framework: Optional[str] = None


class AppResponse(BaseModel):
    """App response model."""

    id: str
    name: str
    slug: str
    description: Optional[str]
    environment: str
    framework: Optional[str]
    status: str
    created_at: str
    last_event_at: Optional[str]
    event_count_24h: int = 0
    error_count_24h: int = 0


class ApiKeyResponse(BaseModel):
    """API key response (only shown once on creation)."""

    id: str
    name: str
    key_prefix: str
    key_type: str
    full_key: Optional[str] = None  # Only set on creation
    permissions: list[str]
    created_at: str
    last_used_at: Optional[str]


class EventSummary(BaseModel):
    """Event summary for dashboard."""

    id: str
    event_type: str
    severity: str
    error_type: Optional[str]
    error_message: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]
    status: str
    occurred_at: str
    analysis_status: str
    analysis_summary: Optional[str]


class DashboardStats(BaseModel):
    """Dashboard statistics."""

    total_apps: int
    total_events_24h: int
    total_errors_24h: int
    critical_count: int
    warning_count: int
    apps_healthy: int
    apps_warning: int
    apps_critical: int


class AIAnalysis(BaseModel):
    """AI analysis result."""

    summary: str
    root_cause: str
    suggested_fix: str
    severity_assessment: str
    related_issues: list[str]
    code_suggestions: list[dict[str, str]]
    confidence: float


class EventDetail(BaseModel):
    """Detailed event information including AI analysis."""

    id: str
    app_id: str
    event_type: str
    severity: str
    error_type: Optional[str]
    error_message: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]
    stack_trace: Optional[str]
    environment: Optional[str]
    status: str
    occurred_at: str
    analysis_status: str
    analysis: Optional[AIAnalysis]
    model_used: Optional[str]
    analyzed_at: Optional[str]


# ============================================
# App Endpoints
# ============================================


@router.get("/apps", response_model=list[AppResponse])
async def list_apps(
    user: dict = Depends(get_current_user),
) -> list[AppResponse]:
    """List all apps for the user's organization."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            return []

        # Get apps with event counts
        result = (
            supabase.table("apps")
            .select("*")
            .eq("org_id", user["org_id"])
            .neq("status", "archived")
            .order("created_at", desc=True)
            .execute()
        )

        apps = []
        for app in result.data or []:
            # Get event counts for last 24h
            yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()

            event_count = (
                supabase.table("event_metadata")
                .select("id", count="exact")
                .eq("app_id", app["id"])
                .gte("occurred_at", yesterday)
                .execute()
            )

            error_count = (
                supabase.table("event_metadata")
                .select("id", count="exact")
                .eq("app_id", app["id"])
                .in_("severity", ["critical", "high"])
                .gte("occurred_at", yesterday)
                .execute()
            )

            apps.append(
                AppResponse(
                    id=app["id"],
                    name=app["name"],
                    slug=app["slug"],
                    description=app.get("description"),
                    environment=app["environment"],
                    framework=app.get("framework"),
                    status=app["status"],
                    created_at=app["created_at"],
                    last_event_at=app.get("last_event_at"),
                    event_count_24h=event_count.count or 0,
                    error_count_24h=error_count.count or 0,
                )
            )

        return apps

    except Exception as e:
        logger.exception(f"Failed to list apps: {e}")
        return []


@router.post("/apps", response_model=AppResponse, status_code=status.HTTP_201_CREATED)
async def create_app(
    request: AppCreate,
    user: dict = Depends(get_current_user),
) -> AppResponse:
    """Create a new app."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization not found",
            )

        # Generate slug from name
        import re

        slug = re.sub(r"[^a-zA-Z0-9]+", "-", request.name.lower()).strip("-")

        app_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        app_data = {
            "id": app_id,
            "org_id": user["org_id"],
            "name": request.name,
            "slug": slug,
            "description": request.description,
            "environment": request.environment,
            "framework": request.framework,
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }

        result = supabase.table("apps").insert(app_data).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create app",
            )

        app = result.data[0]

        return AppResponse(
            id=app["id"],
            name=app["name"],
            slug=app["slug"],
            description=app.get("description"),
            environment=app["environment"],
            framework=app.get("framework"),
            status=app["status"],
            created_at=app["created_at"],
            last_event_at=None,
            event_count_24h=0,
            error_count_24h=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create app: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create app",
        )


@router.get("/apps/{app_id}", response_model=AppResponse)
async def get_app(
    app_id: str,
    user: dict = Depends(get_current_user),
) -> AppResponse:
    """Get a specific app."""
    try:
        from api.db import supabase

        if not supabase:
            raise HTTPException(status_code=404, detail="App not found")

        result = (
            supabase.table("apps")
            .select("*")
            .eq("id", app_id)
            .eq("org_id", user["org_id"])
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="App not found")

        app = result.data

        return AppResponse(
            id=app["id"],
            name=app["name"],
            slug=app["slug"],
            description=app.get("description"),
            environment=app["environment"],
            framework=app.get("framework"),
            status=app["status"],
            created_at=app["created_at"],
            last_event_at=app.get("last_event_at"),
            event_count_24h=0,
            error_count_24h=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get app: {e}")
        raise HTTPException(status_code=404, detail="App not found")


@router.delete("/apps/{app_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_app(
    app_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete (archive) an app.

    This soft-deletes the app by setting its status to 'archived'.
    All associated data is retained but the app won't appear in listings.
    """
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            raise HTTPException(status_code=404, detail="App not found")

        # Verify app ownership
        result = (
            supabase.table("apps")
            .select("id")
            .eq("id", app_id)
            .eq("org_id", user["org_id"])
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="App not found")

        # Soft delete by setting status to archived
        supabase.table("apps").update(
            {"status": "archived", "updated_at": datetime.utcnow().isoformat()}
        ).eq("id", app_id).execute()

        logger.info(f"App {app_id} archived by user {user.get('id')}")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete app: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete app")


# ============================================
# API Key Endpoints
# ============================================


@router.get("/apps/{app_id}/keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    app_id: str,
    user: dict = Depends(get_current_user),
) -> list[ApiKeyResponse]:
    """List API keys for an app (without full key values)."""
    try:
        from api.db import supabase

        if not supabase:
            return []

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

        result = (
            supabase.table("api_keys")
            .select("id, name, key_prefix, key_type, permissions, created_at, last_used_at")
            .eq("app_id", app_id)
            .is_("revoked_at", "null")
            .order("created_at", desc=True)
            .execute()
        )

        return [
            ApiKeyResponse(
                id=key["id"],
                name=key["name"],
                key_prefix=key["key_prefix"],
                key_type=key["key_type"],
                permissions=key.get("permissions", []),
                created_at=key["created_at"],
                last_used_at=key.get("last_used_at"),
            )
            for key in result.data or []
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list API keys: {e}")
        return []


@router.post(
    "/apps/{app_id}/keys",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    app_id: str,
    name: str = "Default Key",
    key_type: str = "live",
    user: dict = Depends(get_current_user),
) -> ApiKeyResponse:
    """Create a new API key for an app.

    IMPORTANT: The full key is only returned once on creation.
    Store it securely - it cannot be retrieved again.
    """
    try:
        from api.db import supabase

        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        # Verify app ownership
        app_result = (
            supabase.table("apps")
            .select("id, org_id")
            .eq("id", app_id)
            .eq("org_id", user["org_id"])
            .single()
            .execute()
        )

        if not app_result.data:
            raise HTTPException(status_code=404, detail="App not found")

        # Generate key
        full_key, key_hash = generate_api_key(key_type)
        key_prefix = full_key[:16]  # e.g., "cw_live_aBcDeFgH"

        key_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        key_data = {
            "id": key_id,
            "org_id": user["org_id"],
            "app_id": app_id,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "name": name,
            "key_type": key_type,
            "permissions": ["telemetry:write", "evidence:write", "health:read"],
            "created_by": user["id"],
            "created_at": now,
        }

        result = supabase.table("api_keys").insert(key_data).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key",
            )

        return ApiKeyResponse(
            id=key_id,
            name=name,
            key_prefix=key_prefix,
            key_type=key_type,
            full_key=full_key,  # Only returned on creation!
            permissions=key_data["permissions"],
            created_at=now,
            last_used_at=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def revoke_api_key(
    key_id: str,
    user: dict = Depends(get_current_user),
):
    """Revoke an API key."""
    try:
        from api.db import supabase

        if not supabase:
            raise HTTPException(status_code=404, detail="Key not found")

        # Verify key ownership
        key_result = (
            supabase.table("api_keys")
            .select("id, org_id")
            .eq("id", key_id)
            .eq("org_id", user["org_id"])
            .single()
            .execute()
        )

        if not key_result.data:
            raise HTTPException(status_code=404, detail="Key not found")

        # Revoke the key
        supabase.table("api_keys").update(
            {"revoked_at": datetime.utcnow().isoformat()}
        ).eq("id", key_id).execute()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to revoke API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke key")


# ============================================
# Events Endpoints
# ============================================


@router.get("/apps/{app_id}/events", response_model=list[EventSummary])
async def list_app_events(
    app_id: str,
    user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    severity: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> list[EventSummary]:
    """List events for an app."""
    try:
        from api.db import supabase

        if not supabase:
            return []

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

        query = (
            supabase.table("event_metadata")
            .select("*")
            .eq("app_id", app_id)
            .order("occurred_at", desc=True)
            .limit(limit)
            .offset(offset)
        )

        if severity:
            query = query.eq("severity", severity)

        if status_filter:
            query = query.eq("status", status_filter)

        result = query.execute()

        return [
            EventSummary(
                id=event["id"],
                event_type=event["event_type"],
                severity=event.get("severity", "medium"),
                error_type=event.get("error_type"),
                error_message=event.get("error_message"),
                file_path=event.get("file_path"),
                line_number=event.get("line_number"),
                status=event.get("status", "open"),
                occurred_at=event["occurred_at"],
                analysis_status=event.get("analysis_status", "pending"),
                analysis_summary=event.get("analysis_result", {}).get("summary")
                if event.get("analysis_result")
                else None,
            )
            for event in result.data or []
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list events: {e}")
        return []


@router.get("/events", response_model=list[EventSummary])
async def list_all_events(
    user: dict = Depends(get_current_user),
    limit: int = 50,
    severity: Optional[str] = None,
) -> list[EventSummary]:
    """List recent events across all apps."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            return []

        # Get all app IDs for this org
        apps_result = (
            supabase.table("apps")
            .select("id")
            .eq("org_id", user["org_id"])
            .execute()
        )

        if not apps_result.data:
            return []

        app_ids = [app["id"] for app in apps_result.data]

        query = (
            supabase.table("event_metadata")
            .select("*")
            .in_("app_id", app_ids)
            .order("occurred_at", desc=True)
            .limit(limit)
        )

        if severity:
            query = query.eq("severity", severity)

        result = query.execute()

        return [
            EventSummary(
                id=event["id"],
                event_type=event["event_type"],
                severity=event.get("severity", "medium"),
                error_type=event.get("error_type"),
                error_message=event.get("error_message"),
                file_path=event.get("file_path"),
                line_number=event.get("line_number"),
                status=event.get("status", "open"),
                occurred_at=event["occurred_at"],
                analysis_status=event.get("analysis_status", "pending"),
                analysis_summary=event.get("analysis_result", {}).get("summary")
                if event.get("analysis_result")
                else None,
            )
            for event in result.data or []
        ]

    except Exception as e:
        logger.exception(f"Failed to list events: {e}")
        return []


# ============================================
# Dashboard Stats
# ============================================


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    user: dict = Depends(get_current_user),
) -> DashboardStats:
    """Get dashboard statistics."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            return DashboardStats(
                total_apps=0,
                total_events_24h=0,
                total_errors_24h=0,
                critical_count=0,
                warning_count=0,
                apps_healthy=0,
                apps_warning=0,
                apps_critical=0,
            )

        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()

        # Get apps
        apps_result = (
            supabase.table("apps")
            .select("id, last_event_at")
            .eq("org_id", user["org_id"])
            .neq("status", "archived")
            .execute()
        )

        app_ids = [app["id"] for app in apps_result.data or []]
        total_apps = len(app_ids)

        if not app_ids:
            return DashboardStats(
                total_apps=0,
                total_events_24h=0,
                total_errors_24h=0,
                critical_count=0,
                warning_count=0,
                apps_healthy=total_apps,
                apps_warning=0,
                apps_critical=0,
            )

        # Get event counts
        events_result = (
            supabase.table("event_metadata")
            .select("id, severity", count="exact")
            .in_("app_id", app_ids)
            .gte("occurred_at", yesterday)
            .execute()
        )

        total_events = events_result.count or 0

        # Count by severity
        critical_count = 0
        high_count = 0
        for event in events_result.data or []:
            if event.get("severity") == "critical":
                critical_count += 1
            elif event.get("severity") == "high":
                high_count += 1

        return DashboardStats(
            total_apps=total_apps,
            total_events_24h=total_events,
            total_errors_24h=critical_count + high_count,
            critical_count=critical_count,
            warning_count=high_count,
            apps_healthy=total_apps - (1 if critical_count > 0 else 0),
            apps_warning=1 if high_count > 0 and critical_count == 0 else 0,
            apps_critical=1 if critical_count > 0 else 0,
        )

    except Exception as e:
        logger.exception(f"Failed to get stats: {e}")
        return DashboardStats(
            total_apps=0,
            total_events_24h=0,
            total_errors_24h=0,
            critical_count=0,
            warning_count=0,
            apps_healthy=0,
            apps_warning=0,
            apps_critical=0,
        )


# ============================================
# Event Detail & AI Analysis
# ============================================


@router.get("/events/{event_id}", response_model=EventDetail)
async def get_event_detail(
    event_id: str,
    user: dict = Depends(get_current_user),
) -> EventDetail:
    """Get detailed event information including AI analysis."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            raise HTTPException(status_code=404, detail="Event not found")

        # Get event
        result = (
            supabase.table("event_metadata")
            .select("*, apps!inner(org_id)")
            .eq("id", event_id)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Event not found")

        event = result.data

        # Verify org ownership
        if event.get("apps", {}).get("org_id") != user["org_id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Parse analysis if present
        analysis = None
        if event.get("analysis_result"):
            analysis_data = event["analysis_result"]
            if isinstance(analysis_data, dict):
                analysis = AIAnalysis(
                    summary=analysis_data.get("summary", ""),
                    root_cause=analysis_data.get("root_cause", ""),
                    suggested_fix=analysis_data.get("suggested_fix", ""),
                    severity_assessment=analysis_data.get("severity_assessment", ""),
                    related_issues=analysis_data.get("related_issues", []),
                    code_suggestions=analysis_data.get("code_suggestions", []),
                    confidence=analysis_data.get("confidence", 0.0),
                )

        return EventDetail(
            id=event["id"],
            app_id=event["app_id"],
            event_type=event["event_type"],
            severity=event.get("severity", "medium"),
            error_type=event.get("error_type"),
            error_message=event.get("error_message"),
            file_path=event.get("file_path"),
            line_number=event.get("line_number"),
            stack_trace=event.get("stack_trace"),
            environment=event.get("environment"),
            status=event.get("status", "open"),
            occurred_at=event["occurred_at"],
            analysis_status=event.get("analysis_status", "pending"),
            analysis=analysis,
            model_used=event.get("model_used"),
            analyzed_at=event.get("analyzed_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get event: {e}")
        raise HTTPException(status_code=500, detail="Failed to get event")


@router.post("/events/{event_id}/analyze")
async def trigger_event_analysis(
    event_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
) -> dict[str, str]:
    """Trigger AI analysis for an event."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            raise HTTPException(status_code=404, detail="Event not found")

        # Get event with app ownership check
        result = (
            supabase.table("event_metadata")
            .select("*, apps!inner(org_id)")
            .eq("id", event_id)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Event not found")

        event = result.data

        # Verify org ownership
        if event.get("apps", {}).get("org_id") != user["org_id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Check if already analyzed
        if event.get("analysis_status") == "completed":
            return {"status": "already_analyzed", "event_id": event_id}

        # Check if AI is available
        analyzer = get_analyzer()
        if not analyzer.is_available:
            raise HTTPException(
                status_code=503,
                detail="AI analysis is not available. Please configure an AI API key.",
            )

        # Update status to queued
        supabase.table("event_metadata").update(
            {"analysis_status": "queued"}
        ).eq("id", event_id).execute()

        # Run analysis in background
        async def run_analysis():
            try:
                result = await analyzer.analyze_event(
                    event_type=event.get("event_type", "error"),
                    severity=event.get("severity", "medium"),
                    error_type=event.get("error_type"),
                    error_message=event.get("error_message"),
                    file_path=event.get("file_path"),
                    line_number=event.get("line_number"),
                    stack_trace=event.get("stack_trace"),
                    environment=event.get("environment", "production"),
                    context={},
                )

                if result:
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

                    logger.info(f"Analysis completed for event {event_id}")
                else:
                    supabase.table("event_metadata").update(
                        {"analysis_status": "failed"}
                    ).eq("id", event_id).execute()

            except Exception as e:
                logger.exception(f"Analysis failed for event {event_id}: {e}")
                supabase.table("event_metadata").update(
                    {"analysis_status": "failed"}
                ).eq("id", event_id).execute()

        background_tasks.add_task(run_analysis)

        return {"status": "queued", "event_id": event_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to trigger analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger analysis")


@router.get("/ai/status")
async def get_ai_status(
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Get AI analysis service status."""
    analyzer = get_analyzer()

    return {
        "available": analyzer.is_available,
        "models": [model for model, _ in analyzer._available_models],
        "message": (
            "AI analysis is ready"
            if analyzer.is_available
            else "No AI API keys configured. Add GOOGLE_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY to enable."
        ),
    }


@router.get("/notifications/status")
async def get_notifications_status(
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Get notification service status."""
    notification_service = get_notification_service()

    return {
        "available": notification_service.is_available,
        "channels": notification_service.available_channels,
        "message": (
            f"Notifications available via: {', '.join(notification_service.available_channels)}"
            if notification_service.is_available
            else "No notification channels configured. Add RESEND_API_KEY for email or TELEGRAM_BOT_TOKEN for Telegram."
        ),
    }


@router.post("/events/{event_id}/notify")
async def send_event_notification(
    event_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Manually send notification for an event."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            raise HTTPException(status_code=404, detail="Event not found")

        # Get event with app ownership check
        result = (
            supabase.table("event_metadata")
            .select("*, apps!inner(org_id, name)")
            .eq("id", event_id)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Event not found")

        event = result.data
        app = event.get("apps", {})

        # Verify org ownership
        if app.get("org_id") != user["org_id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get org notification settings
        org_result = (
            supabase.table("organizations")
            .select("notification_email, telegram_chat_id")
            .eq("id", user["org_id"])
            .single()
            .execute()
        )

        if not org_result.data:
            raise HTTPException(status_code=404, detail="Organization not found")

        org = org_result.data
        notification_service = get_notification_service()

        if not notification_service.is_available:
            raise HTTPException(
                status_code=503,
                detail="No notification channels configured",
            )

        # Send notifications in background
        async def send_notifications():
            results = await notification_service.send_error_alert(
                event=event,
                app_name=app.get("name", "Unknown App"),
                to_email=org.get("notification_email"),
                telegram_chat_id=org.get("telegram_chat_id"),
            )
            for r in results:
                if r.success:
                    logger.info(f"Notification sent via {r.channel}")
                else:
                    logger.warning(f"Notification failed via {r.channel}: {r.error}")

        background_tasks.add_task(send_notifications)

        return {
            "status": "queued",
            "channels": notification_service.available_channels,
            "event_id": event_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to send notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")


# ============================================
# Settings Endpoints
# ============================================


class PlanInfo(BaseModel):
    """Plan tier information."""

    plan: str
    plan_limits: dict
    is_paid: bool = False
    is_partner: bool = False
    is_admin: bool = False


class OrganizationSettings(BaseModel):
    """Organization settings model."""

    name: str
    plan_info: Optional[PlanInfo] = None
    notification_email: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    slack_webhook: Optional[str] = None
    notify_on_critical: bool = True
    notify_on_warning: bool = True
    weekly_digest: bool = True


class UpdateSettingsRequest(BaseModel):
    """Request to update organization settings."""

    notification_email: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    slack_webhook: Optional[str] = None
    notify_on_critical: Optional[bool] = None
    notify_on_warning: Optional[bool] = None
    weekly_digest: Optional[bool] = None


@router.get("/settings", response_model=OrganizationSettings)
async def get_settings(
    user: dict = Depends(get_current_user),
) -> OrganizationSettings:
    """Get organization settings."""
    try:
        from api.auth.api_key import get_plan_limits
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            raise HTTPException(status_code=404, detail="Organization not found")

        result = (
            supabase.table("organizations")
            .select("*")
            .eq("id", user["org_id"])
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Organization not found")

        org = result.data
        plan = org.get("plan", "hobbyist")
        plan_limits = get_plan_limits(plan)

        plan_info = PlanInfo(
            plan=plan,
            plan_limits=plan_limits,
            is_paid=plan_limits.get("is_paid", False),
            is_partner=plan == "partner",
            is_admin=plan == "admin",
        )

        return OrganizationSettings(
            name=org.get("name", "My Organization"),
            plan_info=plan_info,
            notification_email=org.get("notification_email"),
            telegram_chat_id=org.get("telegram_chat_id"),
            slack_webhook=org.get("slack_webhook"),
            notify_on_critical=org.get("notify_on_critical", True),
            notify_on_warning=org.get("notify_on_warning", True),
            weekly_digest=org.get("weekly_digest", True),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get settings")


@router.patch("/settings", response_model=OrganizationSettings)
async def update_settings(
    request: UpdateSettingsRequest,
    user: dict = Depends(get_current_user),
) -> OrganizationSettings:
    """Update organization settings."""
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            raise HTTPException(status_code=404, detail="Organization not found")

        # Build update data (only include non-None values)
        update_data = {}
        if request.notification_email is not None:
            update_data["notification_email"] = request.notification_email
        if request.telegram_chat_id is not None:
            update_data["telegram_chat_id"] = request.telegram_chat_id
        if request.slack_webhook is not None:
            update_data["slack_webhook"] = request.slack_webhook
        if request.notify_on_critical is not None:
            update_data["notify_on_critical"] = request.notify_on_critical
        if request.notify_on_warning is not None:
            update_data["notify_on_warning"] = request.notify_on_warning
        if request.weekly_digest is not None:
            update_data["weekly_digest"] = request.weekly_digest

        if not update_data:
            # No changes, just return current settings
            return await get_settings(user)

        update_data["updated_at"] = datetime.utcnow().isoformat()

        result = (
            supabase.table("organizations")
            .update(update_data)
            .eq("id", user["org_id"])
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update settings")

        # Return updated settings
        return await get_settings(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update settings")


# ============================================
# Service Infrastructure Endpoints
# ============================================


class ServiceNode(BaseModel):
    """A service in the architecture map."""

    id: str
    type: str  # 'database', 'api', 'external', 'cache', 'frontend', 'storage'
    name: str
    status: str  # 'healthy', 'warning', 'critical'
    latency: Optional[float] = None
    error_rate: Optional[float] = None
    url: Optional[str] = None
    last_checked: Optional[str] = None


class ServiceEdge(BaseModel):
    """A connection between services."""

    id: str
    source: str
    target: str
    label: Optional[str] = None


class ArchitectureMap(BaseModel):
    """Full architecture map for an app."""

    nodes: list[ServiceNode]
    edges: list[ServiceEdge]


@router.get("/apps/{app_id}/architecture", response_model=ArchitectureMap)
async def get_architecture_map(
    app_id: str,
    user: dict = Depends(get_current_user),
) -> ArchitectureMap:
    """Get architecture map for an app.

    This returns the connected services (databases, APIs, external services)
    that the app uses, along with their health status.
    """
    try:
        from api.db import supabase

        if not supabase or not user.get("org_id"):
            raise HTTPException(status_code=404, detail="App not found")

        # Verify app ownership
        app_result = (
            supabase.table("apps")
            .select("*, config")
            .eq("id", app_id)
            .eq("org_id", user["org_id"])
            .single()
            .execute()
        )

        if not app_result.data:
            raise HTTPException(status_code=404, detail="App not found")

        app = app_result.data
        config = app.get("config", {})

        # Build architecture from app config
        # The SDK can report connected services via telemetry
        nodes: list[ServiceNode] = []
        edges: list[ServiceEdge] = []

        # Always include the app itself as the central node
        nodes.append(
            ServiceNode(
                id="app",
                type="api",
                name=app.get("name", "Application"),
                status=app.get("status", "healthy"),
                url=config.get("app_url"),
            )
        )

        # Get connected services from config
        services = config.get("services", [])

        for i, service in enumerate(services):
            node_id = f"service_{i}"
            nodes.append(
                ServiceNode(
                    id=node_id,
                    type=service.get("type", "external"),
                    name=service.get("name", f"Service {i + 1}"),
                    status=service.get("status", "healthy"),
                    latency=service.get("latency"),
                    error_rate=service.get("error_rate"),
                    url=service.get("url"),
                    last_checked=service.get("last_checked"),
                )
            )
            edges.append(
                ServiceEdge(
                    id=f"edge_{i}",
                    source="app",
                    target=node_id,
                    label=service.get("connection_type"),
                )
            )

        # If no services configured, return default architecture
        if len(nodes) == 1:
            # Add common default services based on framework
            framework = app.get("framework", "").lower()

            # Database node
            nodes.append(
                ServiceNode(
                    id="database",
                    type="database",
                    name="Database",
                    status="healthy",
                )
            )
            edges.append(
                ServiceEdge(id="edge_db", source="app", target="database")
            )

            # Cache node (if Redis/cache detected)
            nodes.append(
                ServiceNode(
                    id="cache",
                    type="cache",
                    name="Cache (Redis)",
                    status="healthy",
                )
            )
            edges.append(
                ServiceEdge(id="edge_cache", source="app", target="cache")
            )

            # External API node
            nodes.append(
                ServiceNode(
                    id="external",
                    type="external",
                    name="External APIs",
                    status="healthy",
                )
            )
            edges.append(
                ServiceEdge(id="edge_ext", source="app", target="external")
            )

        return ArchitectureMap(nodes=nodes, edges=edges)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get architecture: {e}")
        raise HTTPException(status_code=500, detail="Failed to get architecture")
