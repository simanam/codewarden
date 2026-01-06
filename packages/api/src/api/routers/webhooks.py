"""CodeWarden Webhooks Router - Incoming webhook handlers.

Handles webhooks from:
- Telegram bot updates
- GitHub events (future)
- Stripe payments (future)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status

from api.services.telegram_bot import get_telegram_bot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ============================================
# Telegram Webhook
# ============================================


@router.post(
    "/telegram",
    summary="Telegram webhook",
    description="Receives updates from Telegram bot.",
)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None),
) -> dict[str, str]:
    """
    Handle incoming Telegram updates.

    This endpoint receives webhook updates from Telegram when users
    interact with the CodeWarden bot.
    """
    try:
        update = await request.json()
        logger.debug(f"Received Telegram update: {update.get('update_id')}")

        bot = get_telegram_bot()

        # Handle the update
        response = await bot.handle_update(update)

        if response:
            # Get chat_id from the update
            message = update.get("message") or update.get("callback_query", {}).get("message")
            if message:
                chat_id = str(message.get("chat", {}).get("id", ""))

                if chat_id:
                    # Send response back to user
                    await bot.send_message(
                        chat_id=chat_id,
                        text=response.text,
                        parse_mode=response.parse_mode,
                        reply_markup=response.reply_markup,
                    )

        return {"status": "ok"}

    except Exception as e:
        logger.exception(f"Telegram webhook error: {e}")
        # Always return 200 to Telegram to prevent retries
        return {"status": "error", "message": str(e)}


@router.post(
    "/telegram/verify",
    summary="Verify Telegram activation code",
    description="Verify a Telegram activation code and link the account.",
)
async def verify_telegram_code(
    code: str,
    org_id: str,
) -> dict[str, Any]:
    """
    Verify a Telegram activation code.

    This is called from the dashboard when a user enters their
    activation code to link their Telegram account.
    """
    bot = get_telegram_bot()

    activation = await bot.verify_activation(code, org_id)

    if not activation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "invalid_code",
                    "message": "Invalid or expired activation code.",
                }
            },
        )

    # In production, save the link to database here
    # INSERT INTO telegram_links (org_id, chat_id, user_id, username, linked_at)

    # Send confirmation to user's Telegram
    await bot.send_message(
        chat_id=activation["chat_id"],
        text="""✅ <b>Account Linked Successfully!</b>

Your Telegram is now connected to CodeWarden.

You will receive:
• Real-time error alerts
• Security vulnerability notifications
• Daily briefings (if enabled)

Use /help to see available commands.
Use /status to check your apps now.""",
    )

    return {
        "success": True,
        "telegram_username": activation.get("username"),
        "linked_at": activation.get("created_at").isoformat() if activation.get("created_at") else None,
    }


# ============================================
# GitHub Webhook (Future)
# ============================================


@router.post(
    "/github",
    summary="GitHub webhook",
    description="Receives events from GitHub (push, PR, etc.).",
)
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
) -> dict[str, str]:
    """
    Handle incoming GitHub webhook events.

    Supports:
    - push: Trigger deployment tracking
    - pull_request: Track PR events
    - security_advisory: Security alerts
    """
    try:
        payload = await request.json()
        logger.info(f"Received GitHub webhook: event={x_github_event}")

        # TODO: Implement GitHub webhook handling
        # - Verify signature
        # - Process events (push, PR, security)
        # - Trigger scans on push to main

        return {"status": "ok", "event": x_github_event or "unknown"}

    except Exception as e:
        logger.exception(f"GitHub webhook error: {e}")
        return {"status": "error", "message": str(e)}


# ============================================
# Stripe Webhook (Future)
# ============================================


@router.post(
    "/stripe",
    summary="Stripe webhook",
    description="Receives payment events from Stripe.",
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(None),
) -> dict[str, str]:
    """
    Handle incoming Stripe webhook events.

    Supports:
    - checkout.session.completed: New subscription
    - customer.subscription.updated: Plan change
    - customer.subscription.deleted: Cancellation
    - invoice.payment_failed: Payment failure
    """
    try:
        payload = await request.body()
        logger.info("Received Stripe webhook")

        # TODO: Implement Stripe webhook handling
        # - Verify signature with stripe.Webhook.construct_event
        # - Process subscription events
        # - Update organization plans

        return {"status": "ok"}

    except Exception as e:
        logger.exception(f"Stripe webhook error: {e}")
        return {"status": "error", "message": str(e)}
