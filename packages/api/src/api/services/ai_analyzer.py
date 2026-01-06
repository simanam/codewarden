"""CodeWarden AI Analyzer Service.

Uses LiteLLM to provide AI-powered analysis of errors and security events.
Supports multiple providers: Google Gemini, Anthropic Claude, OpenAI GPT-4.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import litellm
from litellm import acompletion

from api.config import settings

logger = logging.getLogger(__name__)

# Configure LiteLLM
litellm.set_verbose = settings.debug


@dataclass
class AnalysisResult:
    """Result of AI analysis."""

    summary: str
    root_cause: str
    suggested_fix: str
    severity_assessment: str
    related_issues: list[str]
    code_suggestions: list[dict[str, str]]
    confidence: float
    model_used: str
    analyzed_at: str


class AIAnalyzer:
    """AI-powered event analysis using LiteLLM."""

    # Model priority order - tries each until one works
    MODEL_PRIORITY = [
        ("gemini/gemini-1.5-flash", "google_api_key"),
        ("claude-3-haiku-20240307", "anthropic_api_key"),
        ("gpt-4o-mini", "openai_api_key"),
    ]

    ANALYSIS_PROMPT = """You are a senior software engineer analyzing an error or security event.
Provide a concise, actionable analysis.

Event Details:
- Type: {event_type}
- Severity: {severity}
- Error Type: {error_type}
- Error Message: {error_message}
- File: {file_path}
- Line: {line_number}
- Stack Trace: {stack_trace}
- Environment: {environment}
- Additional Context: {context}

Provide your analysis in the following JSON format:
{{
    "summary": "A one-sentence summary of the issue",
    "root_cause": "What is likely causing this error",
    "suggested_fix": "Step-by-step instructions to fix this issue",
    "severity_assessment": "Your assessment of the actual severity (critical/high/medium/low) and why",
    "related_issues": ["List of related issues or patterns to watch for"],
    "code_suggestions": [
        {{
            "description": "What this change does",
            "before": "problematic code pattern",
            "after": "suggested fix"
        }}
    ],
    "confidence": 0.85
}}

Be specific and practical. Focus on actionable advice."""

    def __init__(self) -> None:
        """Initialize the AI analyzer."""
        self._available_models: list[tuple[str, str]] = []
        self._detect_available_models()

    def _detect_available_models(self) -> None:
        """Detect which AI models are available based on configured API keys."""
        for model, key_name in self.MODEL_PRIORITY:
            key_value = getattr(settings, key_name, "")
            if key_value:
                self._available_models.append((model, key_name))
                logger.info(f"AI model available: {model}")

        if not self._available_models:
            logger.warning("No AI API keys configured. Analysis will be disabled.")

    @property
    def is_available(self) -> bool:
        """Check if any AI model is available."""
        return len(self._available_models) > 0

    def _get_api_key(self, key_name: str) -> str:
        """Get API key by name."""
        return getattr(settings, key_name, "")

    async def analyze_event(
        self,
        event_type: str,
        severity: str,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        stack_trace: Optional[str] = None,
        environment: str = "production",
        context: Optional[dict[str, Any]] = None,
    ) -> Optional[AnalysisResult]:
        """
        Analyze an event using AI.

        Args:
            event_type: Type of event (error, crash, warning, security)
            severity: Severity level (critical, high, medium, low)
            error_type: The exception or error class name
            error_message: The error message
            file_path: File where the error occurred
            line_number: Line number of the error
            stack_trace: Full stack trace if available
            environment: Application environment
            context: Additional context about the event

        Returns:
            AnalysisResult if successful, None if analysis failed
        """
        if not self.is_available:
            logger.warning("No AI models available for analysis")
            return None

        # Format the prompt
        prompt = self.ANALYSIS_PROMPT.format(
            event_type=event_type,
            severity=severity,
            error_type=error_type or "Unknown",
            error_message=error_message or "No message provided",
            file_path=file_path or "Unknown",
            line_number=line_number or "Unknown",
            stack_trace=stack_trace or "Not available",
            environment=environment,
            context=json.dumps(context or {}, indent=2),
        )

        # Try each available model
        for model, key_name in self._available_models:
            try:
                api_key = self._get_api_key(key_name)

                logger.info(f"Attempting analysis with model: {model}")

                response = await acompletion(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful software debugging assistant. Always respond with valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    api_key=api_key,
                    temperature=0.3,
                    max_tokens=1500,
                    response_format={"type": "json_object"},
                )

                # Parse response
                content = response.choices[0].message.content
                if not content:
                    logger.warning(f"Empty response from {model}")
                    continue

                analysis_data = json.loads(content)

                return AnalysisResult(
                    summary=analysis_data.get("summary", "Analysis completed"),
                    root_cause=analysis_data.get("root_cause", "Unknown"),
                    suggested_fix=analysis_data.get("suggested_fix", "No fix suggested"),
                    severity_assessment=analysis_data.get(
                        "severity_assessment", severity
                    ),
                    related_issues=analysis_data.get("related_issues", []),
                    code_suggestions=analysis_data.get("code_suggestions", []),
                    confidence=float(analysis_data.get("confidence", 0.5)),
                    model_used=model,
                    analyzed_at=datetime.now(timezone.utc).isoformat(),
                )

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from {model}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Analysis failed with {model}: {e}")
                continue

        logger.error("All AI models failed to analyze the event")
        return None

    async def analyze_event_batch(
        self,
        events: list[dict[str, Any]],
    ) -> list[tuple[str, Optional[AnalysisResult]]]:
        """
        Analyze a batch of events.

        Args:
            events: List of event dictionaries with event_id and event data

        Returns:
            List of (event_id, AnalysisResult) tuples
        """
        results: list[tuple[str, Optional[AnalysisResult]]] = []

        for event in events:
            event_id = event.get("id", "unknown")
            try:
                result = await self.analyze_event(
                    event_type=event.get("event_type", "error"),
                    severity=event.get("severity", "medium"),
                    error_type=event.get("error_type"),
                    error_message=event.get("error_message"),
                    file_path=event.get("file_path"),
                    line_number=event.get("line_number"),
                    stack_trace=event.get("stack_trace"),
                    environment=event.get("environment", "production"),
                    context=event.get("context"),
                )
                results.append((event_id, result))
            except Exception as e:
                logger.error(f"Failed to analyze event {event_id}: {e}")
                results.append((event_id, None))

        return results


# Singleton instance
_analyzer: Optional[AIAnalyzer] = None


def get_analyzer() -> AIAnalyzer:
    """Get or create the AI analyzer singleton."""
    global _analyzer
    if _analyzer is None:
        _analyzer = AIAnalyzer()
    return _analyzer
