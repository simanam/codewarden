"""CodeWarden Telegram Bot Service.

Provides command handling for the Telegram bot integration.
"""

import hashlib
import hmac
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import httpx

from api.config import settings

logger = logging.getLogger(__name__)


class TelegramCommand(str, Enum):
    """Supported Telegram bot commands."""

    START = "/start"
    STATUS = "/status"
    SCAN = "/scan"
    HELP = "/help"
    UNLINK = "/unlink"


@dataclass
class TelegramMessage:
    """Parsed Telegram message."""

    chat_id: str
    user_id: str
    username: str | None
    text: str
    command: TelegramCommand | None
    args: list[str]


@dataclass
class BotResponse:
    """Bot response to send back."""

    text: str
    parse_mode: str = "HTML"
    reply_markup: dict[str, Any] | None = None


class TelegramBot:
    """Telegram bot for CodeWarden notifications and commands.

    Supports the following commands:
    - /start - Begin pairing with activation code
    - /status - Get current app health summary
    - /scan - Trigger a security scan
    - /help - Show available commands
    - /unlink - Disconnect Telegram from CodeWarden
    """

    def __init__(self, bot_token: str | None = None):
        """Initialize the Telegram bot.

        Args:
            bot_token: Telegram bot token. If not provided, uses settings.
        """
        self.bot_token = bot_token or getattr(settings, "telegram_bot_token", None)
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

        # In-memory store for pending activations (in production, use Redis/DB)
        self._pending_activations: dict[str, dict[str, Any]] = {}

    def parse_message(self, update: dict[str, Any]) -> TelegramMessage | None:
        """Parse a Telegram update into a TelegramMessage.

        Args:
            update: Raw Telegram update object.

        Returns:
            Parsed message or None if not a text message.
        """
        message = update.get("message")
        if not message:
            return None

        text = message.get("text", "")
        chat = message.get("chat", {})
        from_user = message.get("from", {})

        # Parse command and args
        command = None
        args = []

        if text.startswith("/"):
            parts = text.split()
            cmd_text = parts[0].lower().split("@")[0]  # Remove @botname suffix

            try:
                command = TelegramCommand(cmd_text)
            except ValueError:
                pass  # Unknown command

            args = parts[1:]

        return TelegramMessage(
            chat_id=str(chat.get("id", "")),
            user_id=str(from_user.get("id", "")),
            username=from_user.get("username"),
            text=text,
            command=command,
            args=args,
        )

    async def handle_update(self, update: dict[str, Any]) -> BotResponse | None:
        """Handle an incoming Telegram update.

        Args:
            update: Raw Telegram update from webhook.

        Returns:
            Response to send, or None if no response needed.
        """
        message = self.parse_message(update)
        if not message:
            return None

        if not message.command:
            # Not a command, ignore or provide help
            return BotResponse(
                text="I didn't understand that. Use /help to see available commands."
            )

        handlers = {
            TelegramCommand.START: self._handle_start,
            TelegramCommand.STATUS: self._handle_status,
            TelegramCommand.SCAN: self._handle_scan,
            TelegramCommand.HELP: self._handle_help,
            TelegramCommand.UNLINK: self._handle_unlink,
        }

        handler = handlers.get(message.command)
        if handler:
            return await handler(message)

        return BotResponse(text="Unknown command. Use /help to see available commands.")

    async def _handle_start(self, message: TelegramMessage) -> BotResponse:
        """Handle /start command - begin pairing flow.

        Args:
            message: The parsed Telegram message.

        Returns:
            Response with activation code or pairing instructions.
        """
        # Check if already linked (in production, query database)
        # For now, generate activation code

        activation_code = self._generate_activation_code()

        # Store pending activation
        self._pending_activations[activation_code] = {
            "chat_id": message.chat_id,
            "user_id": message.user_id,
            "username": message.username,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=15),
        }

        return BotResponse(
            text=f"""🔐 <b>Welcome to CodeWarden!</b>

To link your account, enter this activation code in your CodeWarden dashboard:

<code>{activation_code}</code>

This code expires in 15 minutes.

<b>Steps:</b>
1. Go to Settings → Integrations in your dashboard
2. Click "Connect Telegram"
3. Enter the code above

Once linked, you'll receive:
• Real-time security alerts
• Error notifications
• Daily briefings

Use /help to see all available commands."""
        )

    async def _handle_status(self, message: TelegramMessage) -> BotResponse:
        """Handle /status command - show app health summary.

        Args:
            message: The parsed Telegram message.

        Returns:
            Response with health status.
        """
        # In production, look up org/apps by chat_id and fetch real data
        # For now, return mock data or prompt to link

        # Check if linked (mock check)
        is_linked = self._is_chat_linked(message.chat_id)

        if not is_linked:
            return BotResponse(
                text="⚠️ Your Telegram is not linked to CodeWarden yet.\n\nUse /start to get an activation code."
            )

        # Mock status (in production, fetch from database)
        return BotResponse(
            text="""📊 <b>CodeWarden Status</b>

<b>Apps Overview:</b>
━━━━━━━━━━━━━━━━━━━━━
✅ <b>my-saas-app</b> - Healthy
   Errors (24h): 3
   Last scan: 2h ago

⚠️ <b>api-backend</b> - Warning
   Errors (24h): 12
   Last scan: 6h ago
━━━━━━━━━━━━━━━━━━━━━

<b>Security Summary:</b>
• Critical: 0
• High: 2
• Medium: 5

<b>Compliance:</b> 83% ready

Use /scan to trigger a security scan."""
        )

    async def _handle_scan(self, message: TelegramMessage) -> BotResponse:
        """Handle /scan command - trigger security scan.

        Args:
            message: The parsed Telegram message.

        Returns:
            Response confirming scan trigger.
        """
        is_linked = self._is_chat_linked(message.chat_id)

        if not is_linked:
            return BotResponse(
                text="⚠️ Your Telegram is not linked to CodeWarden yet.\n\nUse /start to get an activation code."
            )

        # Parse optional app name from args
        app_name = message.args[0] if message.args else None

        if app_name:
            # In production, trigger scan for specific app
            return BotResponse(
                text=f"""🔍 <b>Security Scan Triggered</b>

Scanning: <code>{app_name}</code>
Type: Full scan (dependencies, secrets, code)

You'll receive a notification when the scan completes.

Estimated time: 2-5 minutes"""
            )
        else:
            # Show app selection or scan all
            return BotResponse(
                text="""🔍 <b>Security Scan</b>

Which app would you like to scan?

Use: <code>/scan app-name</code>

Or scan all apps:
<code>/scan all</code>

<b>Available apps:</b>
• my-saas-app
• api-backend"""
            )

    async def _handle_help(self, message: TelegramMessage) -> BotResponse:
        """Handle /help command - show available commands.

        Args:
            message: The parsed Telegram message.

        Returns:
            Response with command list.
        """
        return BotResponse(
            text="""🤖 <b>CodeWarden Bot Commands</b>

<b>Getting Started:</b>
/start - Link your CodeWarden account

<b>Monitoring:</b>
/status - View app health summary
/scan - Trigger a security scan
/scan &lt;app&gt; - Scan a specific app

<b>Account:</b>
/unlink - Disconnect from CodeWarden
/help - Show this help message

<b>What you'll receive:</b>
🔴 Critical error alerts
🟡 Security vulnerability alerts
📊 Daily briefings (if enabled)
✅ Scan completion reports

<b>Need help?</b>
Visit: https://docs.codewarden.io/telegram"""
        )

    async def _handle_unlink(self, message: TelegramMessage) -> BotResponse:
        """Handle /unlink command - disconnect Telegram.

        Args:
            message: The parsed Telegram message.

        Returns:
            Response confirming unlink or asking for confirmation.
        """
        is_linked = self._is_chat_linked(message.chat_id)

        if not is_linked:
            return BotResponse(
                text="ℹ️ Your Telegram is not currently linked to any CodeWarden account."
            )

        # In production, check for confirmation arg or use inline keyboard
        if message.args and message.args[0].lower() == "confirm":
            # Perform unlink
            # In production, update database
            return BotResponse(
                text="""✅ <b>Account Unlinked</b>

Your Telegram has been disconnected from CodeWarden.

You will no longer receive notifications here.

Use /start to link again at any time."""
            )

        return BotResponse(
            text="""⚠️ <b>Confirm Unlink</b>

Are you sure you want to disconnect your Telegram from CodeWarden?

You will stop receiving:
• Error alerts
• Security notifications
• Daily briefings

To confirm, type: <code>/unlink confirm</code>""",
            reply_markup={
                "inline_keyboard": [
                    [
                        {"text": "✅ Confirm Unlink", "callback_data": "unlink_confirm"},
                        {"text": "❌ Cancel", "callback_data": "unlink_cancel"},
                    ]
                ]
            }
        )

    def _generate_activation_code(self) -> str:
        """Generate a 6-character activation code.

        Returns:
            Uppercase alphanumeric code.
        """
        # Generate random bytes and convert to uppercase alphanumeric
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Excludes confusing chars
        return "".join(secrets.choice(alphabet) for _ in range(6))

    def _is_chat_linked(self, chat_id: str) -> bool:
        """Check if a chat is linked to a CodeWarden account.

        Args:
            chat_id: Telegram chat ID.

        Returns:
            True if linked, False otherwise.

        Note:
            In production, this queries the database.
        """
        # Mock implementation - return False for now
        # In production, query telegram_links table
        return False

    async def verify_activation(self, code: str, org_id: str) -> dict[str, Any] | None:
        """Verify and complete an activation code.

        Args:
            code: The activation code from user.
            org_id: Organization ID to link to.

        Returns:
            Activation data if valid, None otherwise.
        """
        activation = self._pending_activations.get(code.upper())

        if not activation:
            return None

        if datetime.utcnow() > activation["expires_at"]:
            del self._pending_activations[code.upper()]
            return None

        # Remove from pending
        del self._pending_activations[code.upper()]

        # In production, save to database:
        # INSERT INTO telegram_links (org_id, chat_id, user_id, username, linked_at)

        return activation

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: dict[str, Any] | None = None,
    ) -> bool:
        """Send a message to a Telegram chat.

        Args:
            chat_id: Target chat ID.
            text: Message text.
            parse_mode: Message format (HTML or Markdown).
            reply_markup: Optional inline keyboard.

        Returns:
            True if sent successfully, False otherwise.
        """
        if not self.api_base:
            logger.warning("Telegram bot token not configured")
            return False

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup

                response = await client.post(
                    f"{self.api_base}/sendMessage",
                    json=payload,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    return True

                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """Verify Telegram webhook signature.

        Args:
            payload: Raw request body.
            signature: X-Telegram-Bot-Api-Secret-Token header.
            secret: Configured webhook secret.

        Returns:
            True if signature is valid.
        """
        # Telegram uses a simple secret token comparison
        return hmac.compare_digest(signature, secret)


# Singleton instance
_bot_instance: TelegramBot | None = None


def get_telegram_bot() -> TelegramBot:
    """Get or create the Telegram bot instance.

    Returns:
        TelegramBot singleton.
    """
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = TelegramBot()
    return _bot_instance
