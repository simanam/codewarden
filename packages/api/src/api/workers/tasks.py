"""CodeWarden Background Worker Tasks.

Uses ARQ (Async Redis Queue) for background job processing.
Tasks include:
- AI event analysis
- Email/notification sending
- Periodic cleanup jobs
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from api.config import settings

logger = logging.getLogger(__name__)

# Redis connection pool
_redis_pool: ArqRedis | None = None


async def get_redis_pool() -> ArqRedis:
    """Get or create the Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = await create_pool(
            RedisSettings.from_dsn(settings.redis_url)
        )
    return _redis_pool


async def enqueue_task(task_name: str, **kwargs: Any) -> str:
    """Enqueue a task for background processing.

    Args:
        task_name: Name of the task function
        **kwargs: Task arguments

    Returns:
        Job ID
    """
    pool = await get_redis_pool()
    job = await pool.enqueue_job(task_name, **kwargs)
    if job:
        logger.info(f"Enqueued task {task_name} with job_id={job.job_id}")
        return job.job_id
    raise RuntimeError(f"Failed to enqueue task {task_name}")


# ============================================
# Task Definitions
# ============================================


async def analyze_event_task(ctx: dict, event_id: str) -> dict[str, Any]:
    """Background task to analyze an event with AI.

    Args:
        ctx: ARQ context (contains redis connection)
        event_id: The event ID to analyze

    Returns:
        Analysis result summary
    """
    logger.info(f"Starting AI analysis for event {event_id}")

    try:
        from api.db import supabase
        from api.services.ai_analyzer import get_analyzer

        if not supabase:
            logger.error("Database not available")
            return {"status": "failed", "error": "Database not available"}

        # Get event data
        result = (
            supabase.table("event_metadata")
            .select("*")
            .eq("id", event_id)
            .single()
            .execute()
        )

        if not result.data:
            logger.warning(f"Event {event_id} not found")
            return {"status": "failed", "error": "Event not found"}

        event = result.data

        # Run AI analysis
        analyzer = get_analyzer()
        if not analyzer.is_available:
            logger.warning("No AI models available")
            supabase.table("event_metadata").update(
                {"analysis_status": "failed"}
            ).eq("id", event_id).execute()
            return {"status": "failed", "error": "No AI models available"}

        analysis = await analyzer.analyze_event(
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

        if analysis:
            # Store analysis result
            analysis_data = {
                "summary": analysis.summary,
                "root_cause": analysis.root_cause,
                "suggested_fix": analysis.suggested_fix,
                "severity_assessment": analysis.severity_assessment,
                "related_issues": analysis.related_issues,
                "code_suggestions": analysis.code_suggestions,
                "confidence": analysis.confidence,
            }

            supabase.table("event_metadata").update(
                {
                    "analysis_status": "completed",
                    "analysis_result": analysis_data,
                    "model_used": analysis.model_used,
                    "analyzed_at": analysis.analyzed_at,
                }
            ).eq("id", event_id).execute()

            logger.info(f"Analysis completed for {event_id} using {analysis.model_used}")

            # Check if we should send notifications
            if event.get("severity") in ["critical", "high"]:
                await enqueue_task(
                    "send_notification_task",
                    event_id=event_id,
                    notification_type="critical_error",
                )

            return {
                "status": "completed",
                "model": analysis.model_used,
                "confidence": analysis.confidence,
            }
        else:
            supabase.table("event_metadata").update(
                {"analysis_status": "failed"}
            ).eq("id", event_id).execute()

            return {"status": "failed", "error": "Analysis returned no result"}

    except Exception as e:
        logger.exception(f"Analysis task failed for {event_id}: {e}")
        try:
            from api.db import supabase

            if supabase:
                supabase.table("event_metadata").update(
                    {"analysis_status": "failed"}
                ).eq("id", event_id).execute()
        except Exception:
            pass

        return {"status": "failed", "error": str(e)}


async def send_notification_task(
    ctx: dict,
    event_id: str,
    notification_type: str = "alert",
) -> dict[str, Any]:
    """Background task to send notifications.

    Args:
        ctx: ARQ context
        event_id: The event that triggered the notification
        notification_type: Type of notification (alert, digest, etc.)

    Returns:
        Notification result
    """
    logger.info(f"Sending {notification_type} notification for event {event_id}")

    try:
        from api.db import supabase

        if not supabase:
            return {"status": "failed", "error": "Database not available"}

        # Get event with app and org info
        result = (
            supabase.table("event_metadata")
            .select("*, apps!inner(name, org_id, config)")
            .eq("id", event_id)
            .single()
            .execute()
        )

        if not result.data:
            return {"status": "failed", "error": "Event not found"}

        event = result.data
        app = event.get("apps", {})

        # Check notification preferences
        config = app.get("config", {})
        if not config.get("notify_on_crash", True):
            logger.info(f"Notifications disabled for app {app.get('name')}")
            return {"status": "skipped", "reason": "notifications_disabled"}

        # Get org notification settings
        org_result = (
            supabase.table("organizations")
            .select("notification_email, slack_webhook, telegram_chat_id")
            .eq("id", app.get("org_id"))
            .single()
            .execute()
        )

        if not org_result.data:
            return {"status": "failed", "error": "Organization not found"}

        org = org_result.data
        notifications_sent = []

        # Send email notification
        if org.get("notification_email") and settings.resend_api_key:
            try:
                await send_email_notification(
                    to_email=org["notification_email"],
                    event=event,
                    app_name=app.get("name", "Unknown App"),
                )
                notifications_sent.append("email")
            except Exception as e:
                logger.error(f"Failed to send email: {e}")

        # Send Telegram notification
        if org.get("telegram_chat_id") and settings.telegram_bot_token:
            try:
                await send_telegram_notification(
                    chat_id=org["telegram_chat_id"],
                    event=event,
                    app_name=app.get("name", "Unknown App"),
                )
                notifications_sent.append("telegram")
            except Exception as e:
                logger.error(f"Failed to send Telegram: {e}")

        return {
            "status": "completed",
            "notifications_sent": notifications_sent,
        }

    except Exception as e:
        logger.exception(f"Notification task failed: {e}")
        return {"status": "failed", "error": str(e)}


async def send_email_notification(
    to_email: str,
    event: dict[str, Any],
    app_name: str,
) -> None:
    """Send email notification using Resend."""
    import httpx

    severity = event.get("severity", "medium")
    error_message = event.get("error_message", "No message")
    analysis = event.get("analysis_result", {})

    subject = f"[CodeWarden] {severity.upper()}: {app_name}"

    html_content = f"""
    <h2>Error Alert from {app_name}</h2>
    <p><strong>Severity:</strong> {severity}</p>
    <p><strong>Error:</strong> {error_message}</p>
    <p><strong>File:</strong> {event.get('file_path', 'Unknown')}:{event.get('line_number', '?')}</p>

    {"<h3>AI Analysis</h3><p>" + analysis.get('summary', '') + "</p>" if analysis else ""}
    {"<p><strong>Suggested Fix:</strong> " + analysis.get('suggested_fix', '') + "</p>" if analysis.get('suggested_fix') else ""}

    <p><a href="https://app.codewarden.io/events/{event.get('id')}">View in Dashboard</a></p>
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": "CodeWarden <alerts@codewarden.io>",
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            },
        )
        response.raise_for_status()
        logger.info(f"Email sent to {to_email}")


async def send_telegram_notification(
    chat_id: str,
    event: dict[str, Any],
    app_name: str,
) -> None:
    """Send Telegram notification."""
    import httpx

    severity = event.get("severity", "medium")
    error_message = event.get("error_message", "No message")
    analysis = event.get("analysis_result", {})

    severity_emoji = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }.get(severity, "⚪")

    message = f"""
{severity_emoji} *{severity.upper()}* - {app_name}

*Error:* `{error_message[:200]}`
*File:* `{event.get('file_path', 'Unknown')}:{event.get('line_number', '?')}`
"""

    if analysis.get("summary"):
        message += f"\n*AI Summary:* {analysis['summary']}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
            },
        )
        response.raise_for_status()
        logger.info(f"Telegram message sent to {chat_id}")


async def cleanup_old_events_task(ctx: dict) -> dict[str, Any]:
    """Periodic task to archive old events."""
    logger.info("Running cleanup task")

    try:
        from api.db import supabase

        if not supabase:
            return {"status": "failed", "error": "Database not available"}

        # Archive events older than 30 days for free tier
        # (Adjust based on plan)
        from datetime import timedelta

        cutoff = (datetime.now(UTC) - timedelta(days=30)).isoformat()

        result = (
            supabase.table("event_metadata")
            .update({"status": "archived"})
            .lt("occurred_at", cutoff)
            .neq("status", "archived")
            .execute()
        )

        archived_count = len(result.data) if result.data else 0
        logger.info(f"Archived {archived_count} old events")

        return {"status": "completed", "archived_count": archived_count}

    except Exception as e:
        logger.exception(f"Cleanup task failed: {e}")
        return {"status": "failed", "error": str(e)}


# ============================================
# Worker Configuration
# ============================================


async def startup(ctx: dict) -> None:
    """Worker startup hook."""
    logger.info("Starting CodeWarden worker...")


async def shutdown(ctx: dict) -> None:
    """Worker shutdown hook."""
    logger.info("Shutting down CodeWarden worker...")


class WorkerSettings:
    """ARQ Worker settings."""

    redis_settings = RedisSettings.from_dsn(settings.redis_url)

    functions = [
        analyze_event_task,
        send_notification_task,
        cleanup_old_events_task,
    ]

    on_startup = startup
    on_shutdown = shutdown

    # Retry settings
    max_tries = 3
    retry_delay = 60  # seconds

    # Job settings
    job_timeout = 300  # 5 minutes
    keep_result = 3600  # 1 hour

    # Cron jobs
    cron_jobs = [
        # Run cleanup daily at 3 AM
        # cron(cleanup_old_events_task, hour=3, minute=0),
    ]
