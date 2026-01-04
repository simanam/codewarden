"""CodeWarden Airlock - PII Scrubbing Engine."""

from __future__ import annotations

import re
from typing import Any

from codewarden.types import Event


class Airlock:
    """PII scrubbing engine for CodeWarden events."""

    # Default PII patterns
    DEFAULT_PATTERNS: dict[str, re.Pattern[str]] = {
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "phone_us": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
        "phone_intl": re.compile(r"\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}"),
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "credit_card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
        "ip_address": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
        "api_key": re.compile(r"\b(sk|pk|api|key|token|secret|password)[-_]?[A-Za-z0-9]{16,}\b", re.IGNORECASE),
    }

    # Replacement masks
    MASKS: dict[str, str] = {
        "email": "[EMAIL]",
        "phone_us": "[PHONE]",
        "phone_intl": "[PHONE]",
        "ssn": "[SSN]",
        "credit_card": "[CARD]",
        "ip_address": "[IP]",
        "api_key": "[REDACTED]",
    }

    def __init__(
        self,
        *,
        additional_patterns: dict[str, re.Pattern[str]] | None = None,
        enabled_patterns: list[str] | None = None,
    ) -> None:
        """
        Initialize Airlock PII scrubber.

        Args:
            additional_patterns: Additional regex patterns to detect
            enabled_patterns: List of pattern names to enable (default: all)
        """
        self._patterns = dict(self.DEFAULT_PATTERNS)
        if additional_patterns:
            self._patterns.update(additional_patterns)

        if enabled_patterns:
            self._patterns = {
                k: v for k, v in self._patterns.items() if k in enabled_patterns
            }

    def scrub(self, text: str) -> str:
        """
        Scrub PII from a text string.

        Args:
            text: Text to scrub

        Returns:
            Scrubbed text with PII replaced by masks
        """
        result = text
        for pattern_name, pattern in self._patterns.items():
            mask = self.MASKS.get(pattern_name, "[REDACTED]")
            result = pattern.sub(mask, result)
        return result

    def scrub_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively scrub PII from a dictionary.

        Args:
            data: Dictionary to scrub

        Returns:
            Dictionary with PII scrubbed from string values
        """
        result: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.scrub(value)
            elif isinstance(value, dict):
                result[key] = self.scrub_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self.scrub(v) if isinstance(v, str) else v for v in value
                ]
            else:
                result[key] = value
        return result

    def scrub_event(self, event: Event) -> Event:
        """
        Scrub PII from a CodeWarden event.

        Args:
            event: Event to scrub

        Returns:
            Event with PII scrubbed
        """
        scrubbed = dict(event)

        # Scrub message
        if "message" in scrubbed and scrubbed["message"]:
            scrubbed["message"] = self.scrub(scrubbed["message"])

        # Scrub exception value
        if "exception" in scrubbed and scrubbed["exception"]:
            exc = dict(scrubbed["exception"])
            if exc.get("value"):
                exc["value"] = self.scrub(exc["value"])
            scrubbed["exception"] = exc  # type: ignore[typeddict-item]

        # Scrub context
        if "context" in scrubbed:
            scrubbed["context"] = self.scrub_dict(scrubbed["context"])  # type: ignore[typeddict-item]

        # Scrub extra
        if "extra" in scrubbed:
            scrubbed["extra"] = self.scrub_dict(scrubbed["extra"])  # type: ignore[typeddict-item]

        return scrubbed  # type: ignore[return-value]
