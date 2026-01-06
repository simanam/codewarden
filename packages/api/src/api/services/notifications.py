"""CodeWarden Notification Service.

Handles sending notifications via:
- Email (Resend)
- Telegram
- Slack (future)
- Webhooks (future)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import httpx

from api.config import settings

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    """Result of a notification attempt."""

    channel: str
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class NotificationService:
    """Service for sending notifications across multiple channels."""

    def __init__(self) -> None:
        """Initialize the notification service."""
        self._channels: list[str] = []
        self._detect_available_channels()

    def _detect_available_channels(self) -> None:
        """Detect which notification channels are configured."""
        if settings.resend_api_key:
            self._channels.append("email")
            logger.info("Notification channel available: email (Resend)")

        if settings.telegram_bot_token:
            self._channels.append("telegram")
            logger.info("Notification channel available: telegram")

        if not self._channels:
            logger.warning("No notification channels configured")

    @property
    def available_channels(self) -> list[str]:
        """Get list of available notification channels."""
        return self._channels.copy()

    @property
    def is_available(self) -> bool:
        """Check if any notification channel is available."""
        return len(self._channels) > 0

    async def send_error_alert(
        self,
        event: dict[str, Any],
        app_name: str,
        to_email: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
    ) -> list[NotificationResult]:
        """Send error alert notifications.

        Args:
            event: Event data
            app_name: Name of the app that generated the error
            to_email: Email address to send to
            telegram_chat_id: Telegram chat ID to send to

        Returns:
            List of notification results
        """
        results: list[NotificationResult] = []

        if to_email and "email" in self._channels:
            result = await self.send_email(
                to_email=to_email,
                subject=self._format_error_subject(event, app_name),
                html_content=self._format_error_email(event, app_name),
            )
            results.append(result)

        if telegram_chat_id and "telegram" in self._channels:
            result = await self.send_telegram(
                chat_id=telegram_chat_id,
                message=self._format_error_telegram(event, app_name),
            )
            results.append(result)

        return results

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str = "CodeWarden <alerts@codewarden.io>",
    ) -> NotificationResult:
        """Send an email via Resend.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email body
            from_email: Sender email

        Returns:
            NotificationResult
        """
        if "email" not in self._channels:
            return NotificationResult(
                channel="email",
                success=False,
                error="Email channel not configured",
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {settings.resend_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": from_email,
                        "to": [to_email],
                        "subject": subject,
                        "html": html_content,
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Email sent successfully to {to_email}")
                    return NotificationResult(
                        channel="email",
                        success=True,
                        message_id=data.get("id"),
                    )
                else:
                    error = response.text
                    logger.error(f"Failed to send email: {error}")
                    return NotificationResult(
                        channel="email",
                        success=False,
                        error=error,
                    )

        except Exception as e:
            logger.exception(f"Email sending error: {e}")
            return NotificationResult(
                channel="email",
                success=False,
                error=str(e),
            )

    async def send_telegram(
        self,
        chat_id: str,
        message: str,
        parse_mode: str = "Markdown",
    ) -> NotificationResult:
        """Send a Telegram message.

        Args:
            chat_id: Telegram chat ID
            message: Message text
            parse_mode: Markdown or HTML

        Returns:
            NotificationResult
        """
        if "telegram" not in self._channels:
            return NotificationResult(
                channel="telegram",
                success=False,
                error="Telegram channel not configured",
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": parse_mode,
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Telegram message sent to {chat_id}")
                    return NotificationResult(
                        channel="telegram",
                        success=True,
                        message_id=str(data.get("result", {}).get("message_id")),
                    )
                else:
                    error = response.text
                    logger.error(f"Failed to send Telegram: {error}")
                    return NotificationResult(
                        channel="telegram",
                        success=False,
                        error=error,
                    )

        except Exception as e:
            logger.exception(f"Telegram sending error: {e}")
            return NotificationResult(
                channel="telegram",
                success=False,
                error=str(e),
            )

    def _format_error_subject(self, event: dict[str, Any], app_name: str) -> str:
        """Format email subject for error alert."""
        severity = event.get("severity", "medium").upper()
        error_type = event.get("error_type", "Error")
        return f"[{severity}] {error_type} in {app_name}"

    def _format_error_email(self, event: dict[str, Any], app_name: str) -> str:
        """Format HTML email content for error alert."""
        severity = event.get("severity", "medium")
        error_type = event.get("error_type", "Unknown Error")
        error_message = event.get("error_message", "No message provided")
        file_path = event.get("file_path", "Unknown")
        line_number = event.get("line_number", "?")
        event_id = event.get("id", "unknown")

        # Get analysis if available
        analysis = event.get("analysis_result", {})
        analysis_html = ""
        if analysis:
            analysis_html = f"""
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h3 style="margin-top: 0; color: #333;">AI Analysis</h3>
                <p><strong>Summary:</strong> {analysis.get('summary', 'N/A')}</p>
                <p><strong>Root Cause:</strong> {analysis.get('root_cause', 'N/A')}</p>
                <p><strong>Suggested Fix:</strong> {analysis.get('suggested_fix', 'N/A')}</p>
            </div>
            """

        severity_colors = {
            "critical": "#dc2626",
            "high": "#ea580c",
            "medium": "#ca8a04",
            "low": "#16a34a",
        }
        color = severity_colors.get(severity, "#6b7280")

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">
                    🛡️ CodeWarden Alert
                </h1>
            </div>

            <div style="background: white; padding: 20px; border: 1px solid #e5e7eb; border-top: none;">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <span style="background: {color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; text-transform: uppercase;">
                        {severity}
                    </span>
                    <span style="margin-left: 10px; color: #6b7280; font-size: 14px;">
                        {app_name}
                    </span>
                </div>

                <h2 style="margin: 0 0 10px 0; color: #111;">{error_type}</h2>
                <p style="background: #fef2f2; border-left: 4px solid {color}; padding: 10px 15px; margin: 15px 0; font-family: monospace; font-size: 14px;">
                    {error_message}
                </p>

                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <tr>
                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">File</td>
                        <td style="padding: 8px 0; font-family: monospace; font-size: 14px;">{file_path}:{line_number}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">Event ID</td>
                        <td style="padding: 8px 0; font-family: monospace; font-size: 14px;">{event_id}</td>
                    </tr>
                </table>

                {analysis_html}

                <div style="margin-top: 25px;">
                    <a href="https://app.codewarden.io/events/{event_id}"
                       style="display: inline-block; background: #2563eb; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 500;">
                        View in Dashboard →
                    </a>
                </div>
            </div>

            <div style="background: #f9fafb; padding: 15px 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px; text-align: center; color: #6b7280; font-size: 12px;">
                <p style="margin: 0;">
                    You're receiving this because you have alerts enabled for {app_name}.
                    <br>
                    <a href="https://app.codewarden.io/settings/notifications" style="color: #2563eb;">Manage notification settings</a>
                </p>
            </div>
        </body>
        </html>
        """

    def _format_error_telegram(self, event: dict[str, Any], app_name: str) -> str:
        """Format Telegram message for error alert."""
        severity = event.get("severity", "medium")
        error_type = event.get("error_type", "Error")
        error_message = event.get("error_message", "No message")
        file_path = event.get("file_path", "Unknown")
        line_number = event.get("line_number", "?")
        event_id = event.get("id", "unknown")

        emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }.get(severity, "⚪")

        analysis = event.get("analysis_result", {})
        analysis_text = ""
        if analysis.get("summary"):
            analysis_text = f"\n\n💡 *AI Summary:* {analysis['summary']}"

        return f"""
{emoji} *{severity.upper()}* - {app_name}

*{error_type}*
`{error_message[:200]}`

📁 `{file_path}:{line_number}`
🆔 `{event_id}`{analysis_text}

[View Details](https://app.codewarden.io/events/{event_id})
"""


    async def send_daily_brief(
        self,
        to_email: str,
        org_id: str,
        stats: dict[str, Any],
        apps: list[dict[str, Any]],
    ) -> NotificationResult:
        """Send daily brief email.

        Args:
            to_email: Recipient email
            org_id: Organization ID
            stats: Dashboard statistics
            apps: List of apps with their status

        Returns:
            NotificationResult
        """
        if "email" not in self._channels:
            return NotificationResult(
                channel="email",
                success=False,
                error="Email channel not configured",
            )

        subject = f"📊 CodeWarden Daily Brief - {datetime.now().strftime('%B %d, %Y')}"
        html_content = self._format_daily_brief_email(stats, apps)

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
        )

    def _format_daily_brief_email(
        self,
        stats: dict[str, Any],
        apps: list[dict[str, Any]],
    ) -> str:
        """Format HTML email for daily brief."""
        total_events = stats.get("total_events_24h", 0)
        total_errors = stats.get("total_errors_24h", 0)
        critical_count = stats.get("critical_count", 0)
        apps_healthy = stats.get("apps_healthy", 0)
        total_apps = stats.get("total_apps", 0)

        # Status color
        if critical_count > 0:
            status_color = "#dc2626"
            status_emoji = "🔴"
            status_text = "Critical Issues Detected"
        elif total_errors > 0:
            status_color = "#ea580c"
            status_emoji = "🟠"
            status_text = "Warnings Detected"
        else:
            status_color = "#16a34a"
            status_emoji = "🟢"
            status_text = "All Systems Healthy"

        # Build apps list HTML
        apps_html = ""
        for app in apps[:5]:
            app_status = "🟢" if app.get("error_count_24h", 0) == 0 else "🔴"
            apps_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">
                    {app_status} {app.get('name', 'Unknown')}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    {app.get('event_count_24h', 0)}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    {app.get('error_count_24h', 0)}
                </td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">
                    📊 Daily Brief
                </h1>
                <p style="color: #94a3b8; margin: 5px 0 0 0;">
                    {datetime.now().strftime('%B %d, %Y')}
                </p>
            </div>

            <div style="background: white; padding: 20px; border: 1px solid #e5e7eb; border-top: none;">
                <!-- Status Banner -->
                <div style="background: {status_color}15; border-left: 4px solid {status_color}; padding: 15px; margin-bottom: 20px; border-radius: 0 5px 5px 0;">
                    <span style="font-size: 20px;">{status_emoji}</span>
                    <span style="font-weight: bold; color: {status_color}; margin-left: 10px;">{status_text}</span>
                </div>

                <!-- Stats Grid -->
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px;">
                    <div style="text-align: center; padding: 15px; background: #f9fafb; border-radius: 8px;">
                        <div style="font-size: 24px; font-weight: bold; color: #111;">{total_events}</div>
                        <div style="font-size: 12px; color: #6b7280;">Events (24h)</div>
                    </div>
                    <div style="text-align: center; padding: 15px; background: #f9fafb; border-radius: 8px;">
                        <div style="font-size: 24px; font-weight: bold; color: #dc2626;">{total_errors}</div>
                        <div style="font-size: 12px; color: #6b7280;">Errors</div>
                    </div>
                    <div style="text-align: center; padding: 15px; background: #f9fafb; border-radius: 8px;">
                        <div style="font-size: 24px; font-weight: bold; color: #16a34a;">{apps_healthy}</div>
                        <div style="font-size: 12px; color: #6b7280;">Healthy Apps</div>
                    </div>
                    <div style="text-align: center; padding: 15px; background: #f9fafb; border-radius: 8px;">
                        <div style="font-size: 24px; font-weight: bold; color: #111;">{total_apps}</div>
                        <div style="font-size: 12px; color: #6b7280;">Total Apps</div>
                    </div>
                </div>

                <!-- Apps Table -->
                <h3 style="margin-bottom: 10px;">App Status</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f9fafb;">
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #e5e7eb;">App</th>
                            <th style="padding: 10px; text-align: center; border-bottom: 2px solid #e5e7eb;">Events</th>
                            <th style="padding: 10px; text-align: center; border-bottom: 2px solid #e5e7eb;">Errors</th>
                        </tr>
                    </thead>
                    <tbody>
                        {apps_html if apps_html else '<tr><td colspan="3" style="padding: 20px; text-align: center; color: #6b7280;">No apps configured yet</td></tr>'}
                    </tbody>
                </table>

                <!-- CTA -->
                <div style="margin-top: 25px; text-align: center;">
                    <a href="https://app.codewarden.io/dashboard"
                       style="display: inline-block; background: #2563eb; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 500;">
                        View Full Dashboard →
                    </a>
                </div>
            </div>

            <div style="background: #f9fafb; padding: 15px 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px; text-align: center; color: #6b7280; font-size: 12px;">
                <p style="margin: 0;">
                    You're receiving this daily brief because you have it enabled.
                    <br>
                    <a href="https://app.codewarden.io/settings/notifications" style="color: #2563eb;">Manage notification settings</a>
                </p>
            </div>
        </body>
        </html>
        """


# Singleton instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get or create the notification service singleton."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
