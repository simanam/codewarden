"""API Key authentication for CodeWarden SDK requests."""

import hashlib
import secrets
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from api.config import settings


# API Key header scheme
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


# Plan tiers with their capabilities
PLAN_TIERS = {
    "hobbyist": {
        "events_per_month": 1000,
        "apps_limit": 1,
        "retention_days": 7,
        "ai_analysis": False,
        "security_scans": False,
        "evidence_locker": False,
        "team_members": 1,
        "is_paid": False,
    },
    "builder": {
        "events_per_month": 10000,
        "apps_limit": 3,
        "retention_days": 30,
        "ai_analysis": True,
        "security_scans": "basic",
        "evidence_locker": False,
        "team_members": 1,
        "is_paid": True,
    },
    "pro": {
        "events_per_month": 50000,
        "apps_limit": 10,
        "retention_days": 90,
        "ai_analysis": True,
        "security_scans": "full",
        "evidence_locker": True,
        "team_members": 3,
        "is_paid": True,
    },
    "team": {
        "events_per_month": 200000,
        "apps_limit": 25,
        "retention_days": 180,
        "ai_analysis": True,
        "security_scans": "full",
        "evidence_locker": True,
        "team_members": 10,
        "is_paid": True,
    },
    "enterprise": {
        "events_per_month": -1,  # unlimited
        "apps_limit": -1,
        "retention_days": 365,
        "ai_analysis": True,
        "security_scans": "full",
        "evidence_locker": True,
        "team_members": -1,
        "sso": True,
        "dedicated_support": True,
        "is_paid": True,
    },
    "partner": {
        "events_per_month": -1,  # unlimited
        "apps_limit": -1,
        "retention_days": 365,
        "ai_analysis": True,
        "security_scans": "full",
        "evidence_locker": True,
        "team_members": -1,
        "sso": True,
        "dedicated_support": True,
        "priority_support": True,
        "partner_badge": True,
        "is_paid": False,  # Free for partners
    },
    "admin": {
        "events_per_month": -1,  # unlimited
        "apps_limit": -1,
        "retention_days": -1,  # forever
        "ai_analysis": True,
        "security_scans": "full",
        "evidence_locker": True,
        "team_members": -1,
        "sso": True,
        "dedicated_support": True,
        "admin_access": True,
        "bypass_rate_limits": True,
        "system_admin": True,
        "is_paid": False,
    },
}


def get_plan_limits(plan: str) -> dict:
    """Get the limits and features for a given plan."""
    return PLAN_TIERS.get(plan, PLAN_TIERS["hobbyist"])


def is_unlimited_plan(plan: str) -> bool:
    """Check if a plan has unlimited access (admin or partner or enterprise)."""
    return plan in ("admin", "partner", "enterprise")


def is_admin_plan(plan: str) -> bool:
    """Check if a plan has admin privileges."""
    return plan == "admin"


def plan_has_feature(plan: str, feature: str) -> bool:
    """Check if a plan has a specific feature enabled."""
    if plan == "admin":
        return True  # Admin has all features

    limits = get_plan_limits(plan)
    value = limits.get(feature)

    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value not in ("false", "")
    if isinstance(value, int):
        return value != 0
    return True


def check_plan_limit(plan: str, limit_name: str, current_value: int) -> bool:
    """Check if the current value is within the plan's limit."""
    if plan == "admin":
        return True  # Admin bypasses all limits

    limits = get_plan_limits(plan)
    limit_value = limits.get(limit_name, 0)

    if limit_value == -1:
        return True  # Unlimited

    return current_value < limit_value


@dataclass
class ApiKeyInfo:
    """Information about the authenticated API key."""

    app_id: str
    org_id: str
    app_name: str
    org_plan: str
    permissions: list[str]
    key_type: str  # 'live' or 'test'

    @property
    def plan_limits(self) -> dict:
        """Get the limits for this key's organization plan."""
        return get_plan_limits(self.org_plan)

    @property
    def is_admin(self) -> bool:
        """Check if this is an admin-tier organization."""
        return self.org_plan == "admin"

    @property
    def is_partner(self) -> bool:
        """Check if this is a partner-tier organization."""
        return self.org_plan == "partner"

    @property
    def is_unlimited(self) -> bool:
        """Check if this organization has unlimited access."""
        return is_unlimited_plan(self.org_plan)

    def has_feature(self, feature: str) -> bool:
        """Check if this key's plan has a specific feature."""
        return plan_has_feature(self.org_plan, feature)

    def within_limit(self, limit_name: str, current_value: int) -> bool:
        """Check if a value is within this plan's limits."""
        return check_plan_limit(self.org_plan, limit_name, current_value)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage.

    We use SHA-256 for fast lookups. Since API keys are high-entropy
    (24+ random characters), dictionary attacks are not practical.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key(key_type: str = "live") -> tuple[str, str]:
    """Generate a new API key.

    Returns:
        tuple: (full_key, key_hash)
            - full_key: The complete key to show user once (e.g., cw_live_aBcDeFgH...)
            - key_hash: SHA-256 hash to store in database
    """
    # Generate 24 bytes of random data, base64 encode to ~32 chars
    random_part = secrets.token_urlsafe(24)

    # Format: cw_{type}_{random}
    full_key = f"cw_{key_type}_{random_part}"

    # Hash for storage
    key_hash = hash_api_key(full_key)

    return full_key, key_hash


def extract_api_key(authorization: Optional[str]) -> Optional[str]:
    """Extract API key from Authorization header.

    Supports formats:
    - Bearer cw_live_xxx
    - cw_live_xxx (direct key)
    """
    if not authorization:
        return None

    # Remove "Bearer " prefix if present
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()

    # Check if it looks like a CodeWarden API key
    if authorization.startswith("cw_"):
        return authorization

    return None


async def verify_api_key(
    authorization: Optional[str] = Security(api_key_header),
) -> ApiKeyInfo:
    """Verify an API key and return app info.

    This is a FastAPI dependency that can be used to protect endpoints.

    Usage:
        @app.post("/v1/telemetry")
        async def ingest(api_key: ApiKeyInfo = Depends(verify_api_key)):
            print(f"App: {api_key.app_name}")
    """
    api_key = extract_api_key(authorization)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "missing_api_key",
                    "message": "API key is required. Include 'Authorization: Bearer cw_xxx' header.",
                }
            },
        )

    # Validate key format
    if not api_key.startswith("cw_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "invalid_api_key_format",
                    "message": "Invalid API key format. Keys should start with 'cw_live_' or 'cw_test_'.",
                }
            },
        )

    # Extract key type
    parts = api_key.split("_")
    if len(parts) < 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "invalid_api_key_format",
                    "message": "Invalid API key format. Expected format: cw_live_xxx or cw_test_xxx.",
                }
            },
        )

    key_type = parts[1]

    # Hash the key for database lookup
    key_hash = hash_api_key(api_key)

    # Look up in database
    try:
        from api.db import supabase

        if supabase is None:
            # Development mode without Supabase - allow mock key
            if settings.debug and api_key == "cw_test_development_key":
                return ApiKeyInfo(
                    app_id="dev-app-id",
                    org_id="dev-org-id",
                    app_name="Development App",
                    org_plan="pro",
                    permissions=["telemetry:write", "evidence:write", "health:read"],
                    key_type="test",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "database_unavailable",
                        "message": "Database connection not configured.",
                    }
                },
            )

        # Call the database function to get app info
        result = supabase.rpc(
            "get_app_by_api_key",
            {"p_key_hash": key_hash},
        ).execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "invalid_api_key",
                        "message": "API key is invalid or has been revoked.",
                    }
                },
            )

        app_data = result.data[0]

        # Increment usage counter (fire and forget)
        try:
            supabase.rpc(
                "increment_api_key_usage",
                {"p_key_hash": key_hash},
            ).execute()
        except Exception:
            pass  # Non-critical, don't fail the request

        return ApiKeyInfo(
            app_id=app_data["app_id"],
            org_id=app_data["org_id"],
            app_name=app_data["app_name"],
            org_plan=app_data["org_plan"],
            permissions=app_data.get("permissions", []),
            key_type=key_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        # Log the error but don't expose details
        import logging

        logging.error(f"API key verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "internal_error",
                    "message": "Failed to verify API key.",
                }
            },
        )


def require_permission(permission: str):
    """Dependency factory to check for specific permissions.

    Usage:
        @app.post("/v1/evidence")
        async def log_evidence(
            api_key: ApiKeyInfo = Depends(require_permission("evidence:write"))
        ):
            pass
    """

    async def check_permission(
        api_key: ApiKeyInfo = Security(verify_api_key),
    ) -> ApiKeyInfo:
        if permission not in api_key.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "permission_denied",
                        "message": f"This API key does not have '{permission}' permission.",
                    }
                },
            )
        return api_key

    return check_permission
