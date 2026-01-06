"""Access Logger for authentication and authorization evidence.

Provides structured logging for access events required for SOC 2 compliance.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from codewarden.client import CodeWardenClient
from codewarden.evidence.collector import EvidenceCollector


class AccessAction(str, Enum):
    """Standard access actions for logging."""

    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_RESET = "password_reset"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    API_ACCESS = "api_access"
    RESOURCE_ACCESS = "resource_access"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_DELETED = "account_deleted"
    ACCOUNT_SUSPENDED = "account_suspended"
    SESSION_CREATED = "session_created"
    SESSION_TERMINATED = "session_terminated"


@dataclass
class AccessContext:
    """Context information for an access event."""

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    location: Optional[str] = None
    device_type: Optional[str] = None


class AccessLogger:
    """Log authentication and access events for compliance.

    Provides structured logging of access events with automatic
    context extraction from web frameworks.

    Example:
        >>> from codewarden.evidence import AccessLogger
        >>> logger = AccessLogger()
        >>>
        >>> # Log a login event
        >>> logger.log_login(
        ...     user_id="user123",
        ...     user_email="user@example.com",
        ...     success=True,
        ...     ip_address="192.168.1.1"
        ... )
        >>>
        >>> # Log API access
        >>> logger.log_api_access(
        ...     user_id="user123",
        ...     endpoint="/api/users",
        ...     method="GET",
        ...     status_code=200
        ... )
    """

    def __init__(
        self,
        client: Optional[CodeWardenClient] = None,
        context_extractor: Optional[Callable[[], AccessContext]] = None,
    ):
        """Initialize access logger.

        Args:
            client: CodeWarden client instance
            context_extractor: Optional function to extract context from request
        """
        self._collector = EvidenceCollector(client)
        self._context_extractor = context_extractor

    def _get_context(self, override: Optional[AccessContext] = None) -> AccessContext:
        """Get access context, merging extracted and override values."""
        context = AccessContext()

        # Try to extract context automatically
        if self._context_extractor:
            try:
                context = self._context_extractor()
            except Exception:
                pass

        # Apply overrides
        if override:
            if override.ip_address:
                context.ip_address = override.ip_address
            if override.user_agent:
                context.user_agent = override.user_agent
            if override.session_id:
                context.session_id = override.session_id
            if override.request_id:
                context.request_id = override.request_id
            if override.location:
                context.location = override.location
            if override.device_type:
                context.device_type = override.device_type

        return context

    def log_login(
        self,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
        auth_method: str = "password",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Log a login attempt.

        Args:
            user_id: User identifier
            user_email: User email address
            success: Whether login succeeded
            failure_reason: Reason for failure (if applicable)
            auth_method: Authentication method (password, oauth, sso, etc.)
            ip_address: Client IP address
            user_agent: Client user agent
            metadata: Additional metadata

        Returns:
            Event ID if successful

        Example:
            >>> logger.log_login(
            ...     user_email="user@example.com",
            ...     success=True,
            ...     auth_method="oauth",
            ...     ip_address="192.168.1.1"
            ... )
        """
        action = AccessAction.LOGIN if success else AccessAction.LOGIN_FAILED

        return self._collector.log_access(
            action=action.value,
            resource="authentication",
            user_id=user_id,
            user_email=user_email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "auth_method": auth_method,
                "failure_reason": failure_reason,
                **(metadata or {}),
            },
        )

    def log_logout(
        self,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        session_id: Optional[str] = None,
        reason: str = "user_initiated",
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Log a logout event.

        Args:
            user_id: User identifier
            user_email: User email address
            session_id: Session being terminated
            reason: Reason for logout (user_initiated, timeout, forced, etc.)
            ip_address: Client IP address
            metadata: Additional metadata

        Returns:
            Event ID if successful
        """
        return self._collector.log_access(
            action=AccessAction.LOGOUT.value,
            resource="authentication",
            user_id=user_id,
            user_email=user_email,
            success=True,
            ip_address=ip_address,
            metadata={
                "session_id": session_id,
                "reason": reason,
                **(metadata or {}),
            },
        )

    def log_api_access(
        self,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        endpoint: str = "",
        method: str = "GET",
        status_code: int = 200,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Log an API access event.

        Args:
            user_id: User identifier
            user_email: User email address
            endpoint: API endpoint accessed
            method: HTTP method
            status_code: Response status code
            ip_address: Client IP address
            user_agent: Client user agent
            response_time_ms: Response time in milliseconds
            metadata: Additional metadata

        Returns:
            Event ID if successful

        Example:
            >>> logger.log_api_access(
            ...     user_id="user123",
            ...     endpoint="/api/settings",
            ...     method="PUT",
            ...     status_code=200,
            ...     response_time_ms=45
            ... )
        """
        success = 200 <= status_code < 400

        return self._collector.log_access(
            action=AccessAction.API_ACCESS.value,
            resource=f"{method} {endpoint}",
            user_id=user_id,
            user_email=user_email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                **(metadata or {}),
            },
        )

    def log_resource_access(
        self,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        resource_type: str = "",
        resource_id: str = "",
        action: str = "read",
        success: bool = True,
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Log a resource access event.

        Args:
            user_id: User identifier
            user_email: User email address
            resource_type: Type of resource (project, document, etc.)
            resource_id: Resource identifier
            action: Action performed (read, write, delete, etc.)
            success: Whether access was granted
            ip_address: Client IP address
            metadata: Additional metadata

        Returns:
            Event ID if successful

        Example:
            >>> logger.log_resource_access(
            ...     user_id="user123",
            ...     resource_type="project",
            ...     resource_id="proj_456",
            ...     action="write",
            ...     success=True
            ... )
        """
        return self._collector.log_access(
            action=AccessAction.RESOURCE_ACCESS.value,
            resource=f"{resource_type}:{resource_id}",
            user_id=user_id,
            user_email=user_email,
            success=success,
            ip_address=ip_address,
            metadata={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action_type": action,
                **(metadata or {}),
            },
        )

    def log_permission_change(
        self,
        user_id: str,
        target_user_id: str,
        permission: str,
        granted: bool = True,
        changed_by: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Log a permission change event.

        Args:
            user_id: User making the change
            target_user_id: User receiving/losing permission
            permission: Permission being changed
            granted: True if granting, False if revoking
            changed_by: Who made the change (if different from user_id)
            ip_address: Client IP address
            metadata: Additional metadata

        Returns:
            Event ID if successful

        Example:
            >>> logger.log_permission_change(
            ...     user_id="admin123",
            ...     target_user_id="user456",
            ...     permission="admin",
            ...     granted=True
            ... )
        """
        action = AccessAction.PERMISSION_GRANTED if granted else AccessAction.PERMISSION_REVOKED

        return self._collector.log_access(
            action=action.value,
            resource=f"permission:{permission}",
            user_id=changed_by or user_id,
            success=True,
            ip_address=ip_address,
            metadata={
                "target_user_id": target_user_id,
                "permission": permission,
                "granted": granted,
                "changed_by": changed_by or user_id,
                **(metadata or {}),
            },
        )

    def log_mfa_change(
        self,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        enabled: bool = True,
        mfa_method: str = "totp",
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Log an MFA enable/disable event.

        Args:
            user_id: User identifier
            user_email: User email address
            enabled: True if enabling, False if disabling
            mfa_method: MFA method (totp, sms, email, etc.)
            ip_address: Client IP address
            metadata: Additional metadata

        Returns:
            Event ID if successful
        """
        action = AccessAction.MFA_ENABLED if enabled else AccessAction.MFA_DISABLED

        return self._collector.log_access(
            action=action.value,
            resource="security:mfa",
            user_id=user_id,
            user_email=user_email,
            success=True,
            ip_address=ip_address,
            metadata={
                "mfa_method": mfa_method,
                "enabled": enabled,
                **(metadata or {}),
            },
        )

    def log_password_change(
        self,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        is_reset: bool = False,
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Log a password change/reset event.

        Args:
            user_id: User identifier
            user_email: User email address
            is_reset: True if password reset, False if regular change
            ip_address: Client IP address
            metadata: Additional metadata

        Returns:
            Event ID if successful
        """
        action = AccessAction.PASSWORD_RESET if is_reset else AccessAction.PASSWORD_CHANGE

        return self._collector.log_access(
            action=action.value,
            resource="security:password",
            user_id=user_id,
            user_email=user_email,
            success=True,
            ip_address=ip_address,
            metadata={
                "is_reset": is_reset,
                **(metadata or {}),
            },
        )

    def log_account_lifecycle(
        self,
        user_id: str,
        user_email: Optional[str] = None,
        action: str = "created",
        performed_by: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Log account lifecycle events.

        Args:
            user_id: User identifier
            user_email: User email address
            action: Action (created, deleted, suspended)
            performed_by: Who performed the action
            ip_address: Client IP address
            metadata: Additional metadata

        Returns:
            Event ID if successful
        """
        action_map = {
            "created": AccessAction.ACCOUNT_CREATED,
            "deleted": AccessAction.ACCOUNT_DELETED,
            "suspended": AccessAction.ACCOUNT_SUSPENDED,
        }

        access_action = action_map.get(action, AccessAction.ACCOUNT_CREATED)

        return self._collector.log_access(
            action=access_action.value,
            resource="account",
            user_id=performed_by or user_id,
            user_email=user_email,
            success=True,
            ip_address=ip_address,
            metadata={
                "target_user_id": user_id,
                "account_action": action,
                "performed_by": performed_by,
                **(metadata or {}),
            },
        )
