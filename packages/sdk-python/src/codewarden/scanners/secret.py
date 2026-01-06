"""Secret detection scanner using Gitleaks-derived patterns."""

import os
import re
import time
from pathlib import Path
from typing import Iterator, Optional

from codewarden.scanners.base import BaseScannerModule, ScanResult


class SecretScanner(BaseScannerModule):
    """Scan files for leaked secrets and credentials.

    Uses regex patterns derived from Gitleaks to detect various
    types of secrets including API keys, tokens, passwords, etc.

    Example:
        >>> scanner = SecretScanner(target_path="./src")
        >>> result = scanner.scan()
        >>> for finding in result.findings:
        ...     print(f"Secret found in {finding.file_path}:{finding.line_number}")
    """

    # Gitleaks-derived patterns for secret detection
    PATTERNS: dict[str, dict] = {
        # AWS
        "aws_access_key": {
            "pattern": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
            "severity": "critical",
            "description": "AWS Access Key ID detected",
        },
        "aws_secret_key": {
            "pattern": r"(?i)aws[_\-\.]?(?:secret[_\-\.]?)?(?:access[_\-\.]?)?key['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
            "severity": "critical",
            "description": "AWS Secret Access Key detected",
        },
        # Google
        "google_api_key": {
            "pattern": r"AIza[0-9A-Za-z\-_]{35}",
            "severity": "high",
            "description": "Google API Key detected",
        },
        "google_oauth_client_id": {
            "pattern": r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com",
            "severity": "medium",
            "description": "Google OAuth Client ID detected",
        },
        # GitHub
        "github_token": {
            "pattern": r"gh[pousr]_[A-Za-z0-9_]{36,}",
            "severity": "critical",
            "description": "GitHub Personal Access Token detected",
        },
        "github_app_token": {
            "pattern": r"ghu_[A-Za-z0-9]{36}",
            "severity": "critical",
            "description": "GitHub App Token detected",
        },
        # Stripe
        "stripe_live_key": {
            "pattern": r"sk_live_[0-9a-zA-Z]{24,}",
            "severity": "critical",
            "description": "Stripe Live Secret Key detected",
        },
        "stripe_test_key": {
            "pattern": r"sk_test_[0-9a-zA-Z]{24,}",
            "severity": "medium",
            "description": "Stripe Test Secret Key detected",
        },
        "stripe_publishable": {
            "pattern": r"pk_(?:live|test)_[0-9a-zA-Z]{24,}",
            "severity": "low",
            "description": "Stripe Publishable Key detected (not secret but should review)",
        },
        # Slack
        "slack_token": {
            "pattern": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*",
            "severity": "high",
            "description": "Slack Token detected",
        },
        "slack_webhook": {
            "pattern": r"https://hooks\.slack\.com/services/T[A-Z0-9]{8}/B[A-Z0-9]{8,}/[A-Za-z0-9]{24}",
            "severity": "high",
            "description": "Slack Webhook URL detected",
        },
        # OpenAI
        "openai_api_key": {
            "pattern": r"sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}",
            "severity": "critical",
            "description": "OpenAI API Key detected",
        },
        "openai_api_key_new": {
            "pattern": r"sk-proj-[A-Za-z0-9_-]{80,}",
            "severity": "critical",
            "description": "OpenAI Project API Key detected",
        },
        # Anthropic
        "anthropic_api_key": {
            "pattern": r"sk-ant-[A-Za-z0-9_-]{80,}",
            "severity": "critical",
            "description": "Anthropic API Key detected",
        },
        # JWT
        "jwt_token": {
            "pattern": r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
            "severity": "high",
            "description": "JWT Token detected",
        },
        # Generic patterns
        "private_key": {
            "pattern": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            "severity": "critical",
            "description": "Private Key detected",
        },
        "password_assignment": {
            "pattern": r"(?i)(?:password|passwd|pwd|secret|api[_-]?key|auth[_-]?token)['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]",
            "severity": "high",
            "description": "Hardcoded password or secret detected",
        },
        "bearer_token": {
            "pattern": r"(?i)bearer\s+[a-zA-Z0-9_\-\.=]{20,}",
            "severity": "high",
            "description": "Bearer token detected",
        },
        # Database URLs
        "database_url": {
            "pattern": r"(?:postgres|mysql|mongodb|redis)://[^:]+:[^@]+@[^\s]+",
            "severity": "critical",
            "description": "Database connection string with credentials detected",
        },
        # SendGrid
        "sendgrid_api_key": {
            "pattern": r"SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}",
            "severity": "critical",
            "description": "SendGrid API Key detected",
        },
        # Twilio
        "twilio_api_key": {
            "pattern": r"SK[0-9a-fA-F]{32}",
            "severity": "high",
            "description": "Twilio API Key detected",
        },
        # Mailgun
        "mailgun_api_key": {
            "pattern": r"key-[0-9a-zA-Z]{32}",
            "severity": "high",
            "description": "Mailgun API Key detected",
        },
        # Heroku
        "heroku_api_key": {
            "pattern": r"[hH]eroku[a-zA-Z0-9_\-]*[aA][pP][iI][kK][eE][yY][a-zA-Z0-9_\-]*[=:]['\"]?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}['\"]?",
            "severity": "high",
            "description": "Heroku API Key detected",
        },
        # npm
        "npm_token": {
            "pattern": r"npm_[A-Za-z0-9]{36}",
            "severity": "critical",
            "description": "npm Access Token detected",
        },
        # Discord
        "discord_token": {
            "pattern": r"[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27}",
            "severity": "critical",
            "description": "Discord Bot Token detected",
        },
        "discord_webhook": {
            "pattern": r"https://discord(?:app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+",
            "severity": "high",
            "description": "Discord Webhook URL detected",
        },
    }

    # File extensions to scan
    DEFAULT_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".json",
        ".yml",
        ".yaml",
        ".env",
        ".cfg",
        ".ini",
        ".conf",
        ".config",
        ".sh",
        ".bash",
        ".zsh",
        ".properties",
        ".xml",
        ".toml",
        ".rb",
        ".php",
        ".java",
        ".go",
        ".rs",
        ".cs",
        ".swift",
        ".kt",
        ".gradle",
        ".sql",
        ".tf",
        ".tfvars",
    }

    # Directories to skip
    SKIP_DIRS = {
        ".git",
        ".svn",
        ".hg",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "venv",
        ".venv",
        "env",
        ".env",
        "dist",
        "build",
        ".tox",
        ".eggs",
        "*.egg-info",
    }

    def __init__(
        self,
        target_path: str = ".",
        extensions: Optional[set[str]] = None,
        skip_dirs: Optional[set[str]] = None,
        additional_patterns: Optional[dict] = None,
        max_file_size: int = 1024 * 1024,  # 1MB
        config: Optional[dict] = None,
    ):
        """Initialize secret scanner.

        Args:
            target_path: Directory or file to scan
            extensions: File extensions to scan (default: common code files)
            skip_dirs: Directories to skip
            additional_patterns: Extra patterns to add
            max_file_size: Maximum file size to scan in bytes
            config: Additional configuration
        """
        super().__init__(config)
        self.target_path = Path(target_path)
        self.extensions = extensions or self.DEFAULT_EXTENSIONS
        self.skip_dirs = skip_dirs or self.SKIP_DIRS
        self.max_file_size = max_file_size

        # Compile patterns
        self.compiled_patterns: dict[str, tuple[re.Pattern, dict]] = {}
        patterns = {**self.PATTERNS, **(additional_patterns or {})}
        for name, config in patterns.items():
            try:
                compiled = re.compile(config["pattern"])
                self.compiled_patterns[name] = (compiled, config)
            except re.error as e:
                self._errors.append(f"Invalid pattern '{name}': {e}")

    def is_available(self) -> bool:
        """Secret scanner is always available (no external deps)."""
        return True

    def scan(self) -> ScanResult:
        """Scan files for secrets.

        Returns:
            ScanResult with secret findings
        """
        start_time = time.time()
        self._findings = []
        self._errors = []

        if not self.target_path.exists():
            self._errors.append(f"Target path does not exist: {self.target_path}")
            return self._build_result(start_time)

        try:
            if self.target_path.is_file():
                self._scan_file(self.target_path)
            else:
                for file_path in self._iter_files():
                    self._scan_file(file_path)
        except Exception as e:
            self._errors.append(f"Secret scan error: {str(e)}")

        return self._build_result(start_time)

    def _iter_files(self) -> Iterator[Path]:
        """Iterate over files to scan.

        Yields:
            Path objects for each file to scan
        """
        for root, dirs, files in os.walk(self.target_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]

            for file in files:
                file_path = Path(root) / file

                # Check extension
                if file_path.suffix.lower() not in self.extensions:
                    # Also check for extensionless files like .env
                    if file_path.name not in {".env", ".envrc", "Dockerfile"}:
                        continue

                # Check file size
                try:
                    if file_path.stat().st_size > self.max_file_size:
                        continue
                except OSError:
                    continue

                yield file_path

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single file for secrets.

        Args:
            file_path: Path to file
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            self._errors.append(f"Could not read {file_path}: {e}")
            return

        lines = content.split("\n")
        relative_path = str(file_path.relative_to(self.target_path) if self.target_path.is_dir() else file_path.name)

        for line_num, line in enumerate(lines, start=1):
            # Skip empty lines and comments
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue

            for pattern_name, (compiled, config) in self.compiled_patterns.items():
                matches = compiled.finditer(line)
                for match in matches:
                    # Avoid false positives in documentation or test data
                    if self._is_false_positive(line, match.group(), file_path):
                        continue

                    finding = self._create_finding(
                        type="secret",
                        severity=config.get("severity", "high"),
                        title=config.get("description", f"Secret detected: {pattern_name}"),
                        description=f"Potential {pattern_name.replace('_', ' ')} found in source code",
                        file_path=relative_path,
                        line_number=line_num,
                        column_number=match.start() + 1,
                        remediation=f"Remove the hardcoded secret and use environment variables or a secrets manager instead",
                        raw_data={
                            "pattern_name": pattern_name,
                            "matched_text": self._redact_secret(match.group()),
                            "line_preview": self._redact_line(line),
                        },
                    )
                    self._findings.append(finding)

    def _is_false_positive(self, line: str, match: str, file_path: Path) -> bool:
        """Check if a match is likely a false positive.

        Args:
            line: Full line containing match
            match: Matched text
            file_path: Path to file

        Returns:
            True if likely false positive
        """
        line_lower = line.lower()

        # Skip if line contains common false positive indicators
        false_positive_indicators = [
            "example",
            "sample",
            "placeholder",
            "your_",
            "xxx",
            "fake",
            "test",
            "dummy",
            "<your",
            "${",
            "{{",
            "process.env",
            "os.environ",
            "os.getenv",
        ]
        for indicator in false_positive_indicators:
            if indicator in line_lower:
                return True

        # Skip documentation files
        if file_path.suffix.lower() in {".md", ".rst", ".txt"}:
            return True

        # Skip if the match is all the same character (placeholder)
        if len(set(match.replace("-", "").replace("_", ""))) <= 2:
            return True

        return False

    def _redact_secret(self, secret: str, visible_chars: int = 4) -> str:
        """Redact a secret, showing only first few characters.

        Args:
            secret: Secret to redact
            visible_chars: Number of characters to show

        Returns:
            Redacted string
        """
        if len(secret) <= visible_chars * 2:
            return "*" * len(secret)
        return secret[:visible_chars] + "*" * (len(secret) - visible_chars * 2) + secret[-visible_chars:]

    def _redact_line(self, line: str, max_length: int = 100) -> str:
        """Redact secrets in a line preview.

        Args:
            line: Full line
            max_length: Maximum preview length

        Returns:
            Redacted line preview
        """
        preview = line.strip()
        if len(preview) > max_length:
            preview = preview[:max_length] + "..."

        # Redact any patterns in the preview
        for _, (compiled, _) in self.compiled_patterns.items():
            preview = compiled.sub("[REDACTED]", preview)

        return preview

    def scan_string(self, content: str, source_name: str = "string") -> list:
        """Scan a string for secrets.

        Args:
            content: String content to scan
            source_name: Name to use for findings

        Returns:
            List of findings
        """
        findings = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            for pattern_name, (compiled, config) in self.compiled_patterns.items():
                if compiled.search(line):
                    finding = self._create_finding(
                        type="secret",
                        severity=config.get("severity", "high"),
                        title=config.get("description", f"Secret detected: {pattern_name}"),
                        description=f"Potential {pattern_name.replace('_', ' ')} found",
                        file_path=source_name,
                        line_number=line_num,
                    )
                    findings.append(finding)

        return findings
