"""CodeWarden Dashboard Router - Endpoints for the dashboard frontend.

These endpoints use Supabase JWT authentication (user sessions from dashboard).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field

from api.auth import generate_api_key, hash_api_key
from api.config import settings

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
