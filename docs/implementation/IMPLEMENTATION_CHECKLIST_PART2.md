# CodeWarden Implementation Checklist
## Part 2: Core Product Development (SDK + API)

**Document Version:** 1.0  
**Status:** Ready for Implementation  
**Last Updated:** January 2026  
**Estimated Duration:** Weeks 3-6

---

## Document Navigation

| Part | Focus Area | Status |
|------|------------|--------|
| Part 1 | Foundation & Infrastructure Setup | ✅ Complete |
| **Part 2** | Core Product Development (SDK + API) | 📍 Current |
| Part 3 | Frontend, Integration & Launch | Next |

---

## Prerequisites

Before starting Part 2, ensure:
- [ ] Part 1 completed
- [ ] `./scripts/dev.sh start` runs successfully
- [ ] All external service credentials in `.env`
- [ ] GitHub repository configured with CI/CD

---

# Phase 2: Python SDK Development

## Story 2.1: SDK Project Setup

### Task 2.1.1: Initialize Python SDK Package

**Sub-tasks:**

- [ ] **2.1.1.1** Create package structure
  ```bash
  cd packages/sdk-python
  
  # Initialize with Poetry
  poetry init --name codewarden --description "Security monitoring for solopreneurs" --author "Your Name <you@email.com>" --python "^3.9" --no-interaction
  
  # Create source directory
  mkdir -p codewarden/{middleware,scrubber,scanner,evidence,transport,handshake}
  mkdir -p tests/{unit,integration}
  ```

- [ ] **2.1.1.2** Create `pyproject.toml`
  ```bash
  cat > pyproject.toml << 'EOF'
  [tool.poetry]
  name = "codewarden"
  version = "0.1.0"
  description = "Security monitoring for solopreneurs. You ship the code. We stand guard."
  authors = ["CodeWarden <hello@codewarden.io>"]
  license = "MIT"
  readme = "README.md"
  homepage = "https://codewarden.io"
  repository = "https://github.com/codewarden/codewarden"
  documentation = "https://docs.codewarden.io"
  keywords = ["security", "monitoring", "observability", "fastapi", "sentry"]
  classifiers = [
      "Development Status :: 4 - Beta",
      "Intended Audience :: Developers",
      "License :: OSI Approved :: MIT License",
      "Programming Language :: Python :: 3.9",
      "Programming Language :: Python :: 3.10",
      "Programming Language :: Python :: 3.11",
      "Programming Language :: Python :: 3.12",
      "Framework :: FastAPI",
      "Topic :: System :: Monitoring",
      "Topic :: Security",
  ]
  packages = [{include = "codewarden"}]
  
  [tool.poetry.dependencies]
  python = "^3.9"
  httpx = "^0.27.0"
  pydantic = "^2.5.0"
  pydantic-settings = "^2.1.0"
  structlog = "^24.1.0"
  tenacity = "^8.2.0"
  
  # Optional framework integrations
  fastapi = {version = "^0.109.0", optional = true}
  flask = {version = "^3.0.0", optional = true}
  
  # Security scanning
  pip-audit = {version = "^2.7.0", optional = true}
  bandit = {version = "^1.7.0", optional = true}
  
  [tool.poetry.extras]
  fastapi = ["fastapi"]
  flask = ["flask"]
  security = ["pip-audit", "bandit"]
  all = ["fastapi", "flask", "pip-audit", "bandit"]
  
  [tool.poetry.group.dev.dependencies]
  pytest = "^8.0.0"
  pytest-cov = "^4.1.0"
  pytest-asyncio = "^0.23.0"
  pytest-httpx = "^0.28.0"
  ruff = "^0.2.0"
  mypy = "^1.8.0"
  pre-commit = "^3.6.0"
  
  [tool.ruff]
  line-length = 100
  target-version = "py39"
  
  [tool.ruff.lint]
  select = ["E", "F", "W", "I", "N", "B", "A", "C4", "SIM", "ARG"]
  ignore = ["E501"]
  
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  asyncio_mode = "auto"
  
  [tool.mypy]
  python_version = "3.9"
  strict = true
  
  [tool.coverage.run]
  source = ["codewarden"]
  branch = true
  
  [tool.coverage.report]
  exclude_lines = [
      "pragma: no cover",
      "if TYPE_CHECKING:",
      "raise NotImplementedError",
  ]
  
  [build-system]
  requires = ["poetry-core"]
  build-backend = "poetry.core.masonry.api"
  EOF
  ```

- [ ] **2.1.1.3** Create `codewarden/__init__.py`
  ```bash
  cat > codewarden/__init__.py << 'EOF'
  """
  CodeWarden - Security monitoring for solopreneurs.
  
  You ship the code. We stand guard.
  
  Basic usage:
      from fastapi import FastAPI
      from codewarden import CodeWarden
      
      app = FastAPI()
      warden = CodeWarden(app)
  """
  
  from codewarden.core import CodeWarden
  from codewarden.config import CodeWardenConfig
  
  __version__ = "0.1.0"
  __all__ = ["CodeWarden", "CodeWardenConfig", "__version__"]
  EOF
  ```

- [ ] **2.1.1.4** Create `codewarden/config.py`
  ```bash
  cat > codewarden/config.py << 'EOF'
  """Configuration management for CodeWarden."""
  
  from typing import Optional, List
  from pydantic_settings import BaseSettings
  from pydantic import Field, SecretStr
  
  
  class CodeWardenConfig(BaseSettings):
      """
      CodeWarden configuration.
      
      Can be set via environment variables with CODEWARDEN_ prefix.
      Example: CODEWARDEN_API_KEY=cw_live_xxx
      """
      
      # API Configuration
      api_key: Optional[SecretStr] = Field(
          default=None,
          description="Your CodeWarden API key"
      )
      api_url: str = Field(
          default="https://api.codewarden.io",
          description="CodeWarden API endpoint"
      )
      
      # Feature Flags
      enabled: bool = Field(
          default=True,
          description="Enable/disable CodeWarden"
      )
      scrub_pii: bool = Field(
          default=True,
          description="Enable PII scrubbing before transmission"
      )
      scan_on_startup: bool = Field(
          default=True,
          description="Run vulnerability scan on startup"
      )
      capture_errors: bool = Field(
          default=True,
          description="Capture and report errors"
      )
      capture_requests: bool = Field(
          default=True,
          description="Log request/response metadata"
      )
      evidence_logging: bool = Field(
          default=True,
          description="Enable compliance evidence logging"
      )
      
      # Scrubbing Configuration
      scrub_patterns: List[str] = Field(
          default_factory=lambda: [
              "email", "credit_card", "ssn", "phone",
              "api_key", "password", "jwt"
          ],
          description="PII patterns to scrub"
      )
      
      # Performance
      max_payload_size: int = Field(
          default=65536,  # 64KB
          description="Maximum payload size to send"
      )
      request_timeout: float = Field(
          default=5.0,
          description="Timeout for API requests"
      )
      
      # Environment Detection
      environment: str = Field(
          default="production",
          description="Environment name (production, staging, development)"
      )
      
      model_config = {
          "env_prefix": "CODEWARDEN_",
          "env_file": ".env",
          "extra": "ignore"
      }
  
  
  # Global config instance
  _config: Optional[CodeWardenConfig] = None
  
  
  def get_config() -> CodeWardenConfig:
      """Get or create the global configuration."""
      global _config
      if _config is None:
          _config = CodeWardenConfig()
      return _config
  
  
  def set_config(config: CodeWardenConfig) -> None:
      """Set the global configuration."""
      global _config
      _config = config
  EOF
  ```

- [ ] **2.1.1.5** Install dependencies
  ```bash
  cd packages/sdk-python
  poetry install --all-extras
  ```

**Testing:**
- [ ] Run `poetry check` → No errors
- [ ] Run `poetry run python -c "from codewarden import CodeWarden"` → No import errors

---

### Task 2.1.2: Implement Airlock (PII Scrubber)

**Sub-tasks:**

- [ ] **2.1.2.1** Create `codewarden/scrubber/__init__.py`
  ```bash
  cat > codewarden/scrubber/__init__.py << 'EOF'
  """PII scrubbing module - The Airlock."""
  
  from codewarden.scrubber.airlock import Airlock
  from codewarden.scrubber.patterns import PATTERNS, PatternType
  
  __all__ = ["Airlock", "PATTERNS", "PatternType"]
  EOF
  ```

- [ ] **2.1.2.2** Create `codewarden/scrubber/patterns.py`
  ```bash
  cat > codewarden/scrubber/patterns.py << 'EOF'
  """
  PII detection patterns.
  
  Based on Gitleaks patterns (https://github.com/gitleaks/gitleaks)
  for industry-standard secret detection.
  """
  
  import re
  from enum import Enum
  from typing import Dict, Pattern
  from dataclasses import dataclass
  
  
  class PatternType(Enum):
      """Categories of sensitive data."""
      IDENTITY = "identity"
      FINANCIAL = "financial"
      API_KEY = "api_key"
      AUTH_TOKEN = "auth_token"
      CREDENTIAL = "credential"
  
  
  @dataclass
  class ScrubPattern:
      """A pattern for detecting and scrubbing sensitive data."""
      name: str
      pattern: Pattern
      replacement: str
      category: PatternType
      description: str
  
  
  # ═══════════════════════════════════════════════════════════════
  # IDENTITY PATTERNS
  # ═══════════════════════════════════════════════════════════════
  
  EMAIL_PATTERN = ScrubPattern(
      name="email",
      pattern=re.compile(
          r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
          re.IGNORECASE
      ),
      replacement="[EMAIL_REDACTED]",
      category=PatternType.IDENTITY,
      description="Email addresses"
  )
  
  PHONE_PATTERN = ScrubPattern(
      name="phone",
      pattern=re.compile(
          r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
      ),
      replacement="[PHONE_REDACTED]",
      category=PatternType.IDENTITY,
      description="Phone numbers (US format)"
  )
  
  SSN_PATTERN = ScrubPattern(
      name="ssn",
      pattern=re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
      replacement="[SSN_REDACTED]",
      category=PatternType.IDENTITY,
      description="Social Security Numbers"
  )
  
  # ═══════════════════════════════════════════════════════════════
  # FINANCIAL PATTERNS
  # ═══════════════════════════════════════════════════════════════
  
  CREDIT_CARD_PATTERN = ScrubPattern(
      name="credit_card",
      pattern=re.compile(
          r'\b(?:4[0-9]{12}(?:[0-9]{3})?|'  # Visa
          r'5[1-5][0-9]{14}|'                # MasterCard
          r'3[47][0-9]{13}|'                 # Amex
          r'6(?:011|5[0-9]{2})[0-9]{12}|'   # Discover
          r'(?:2131|1800|35\d{3})\d{11})\b'  # JCB
      ),
      replacement="[CC_REDACTED]",
      category=PatternType.FINANCIAL,
      description="Credit card numbers"
  )
  
  CREDIT_CARD_FORMATTED_PATTERN = ScrubPattern(
      name="credit_card_formatted",
      pattern=re.compile(r'\b(?:\d{4}[- ]?){3}\d{4}\b'),
      replacement="[CC_REDACTED]",
      category=PatternType.FINANCIAL,
      description="Credit card numbers with separators"
  )
  
  # ═══════════════════════════════════════════════════════════════
  # API KEY PATTERNS
  # ═══════════════════════════════════════════════════════════════
  
  OPENAI_KEY_PATTERN = ScrubPattern(
      name="openai_api_key",
      pattern=re.compile(r'sk-[a-zA-Z0-9]{48,}'),
      replacement="[OPENAI_KEY_REDACTED]",
      category=PatternType.API_KEY,
      description="OpenAI API keys"
  )
  
  STRIPE_KEY_PATTERN = ScrubPattern(
      name="stripe_api_key",
      pattern=re.compile(r'sk_(live|test)_[a-zA-Z0-9]{24,}'),
      replacement="[STRIPE_KEY_REDACTED]",
      category=PatternType.API_KEY,
      description="Stripe API keys"
  )
  
  AWS_ACCESS_KEY_PATTERN = ScrubPattern(
      name="aws_access_key",
      pattern=re.compile(r'(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}'),
      replacement="[AWS_KEY_REDACTED]",
      category=PatternType.API_KEY,
      description="AWS Access Key IDs"
  )
  
  AWS_SECRET_KEY_PATTERN = ScrubPattern(
      name="aws_secret_key",
      pattern=re.compile(r'(?i)aws(.{0,20})?[\'"][0-9a-zA-Z/+]{40}[\'"]'),
      replacement="[AWS_SECRET_REDACTED]",
      category=PatternType.API_KEY,
      description="AWS Secret Access Keys"
  )
  
  GOOGLE_API_KEY_PATTERN = ScrubPattern(
      name="google_api_key",
      pattern=re.compile(r'AIza[0-9A-Za-z\-_]{35}'),
      replacement="[GOOGLE_KEY_REDACTED]",
      category=PatternType.API_KEY,
      description="Google API keys"
  )
  
  GITHUB_TOKEN_PATTERN = ScrubPattern(
      name="github_token",
      pattern=re.compile(r'gh[pousr]_[A-Za-z0-9_]{36,}'),
      replacement="[GITHUB_TOKEN_REDACTED]",
      category=PatternType.API_KEY,
      description="GitHub tokens"
  )
  
  SLACK_TOKEN_PATTERN = ScrubPattern(
      name="slack_token",
      pattern=re.compile(r'xox[baprs]-[0-9]{10,13}-[0-9a-zA-Z]{24}'),
      replacement="[SLACK_TOKEN_REDACTED]",
      category=PatternType.API_KEY,
      description="Slack tokens"
  )
  
  # ═══════════════════════════════════════════════════════════════
  # AUTH TOKEN PATTERNS
  # ═══════════════════════════════════════════════════════════════
  
  JWT_PATTERN = ScrubPattern(
      name="jwt",
      pattern=re.compile(r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+'),
      replacement="[JWT_REDACTED]",
      category=PatternType.AUTH_TOKEN,
      description="JSON Web Tokens"
  )
  
  BEARER_TOKEN_PATTERN = ScrubPattern(
      name="bearer_token",
      pattern=re.compile(r'(?i)bearer\s+[a-zA-Z0-9\-_\.]+'),
      replacement="Bearer [TOKEN_REDACTED]",
      category=PatternType.AUTH_TOKEN,
      description="Bearer tokens in headers"
  )
  
  # ═══════════════════════════════════════════════════════════════
  # CREDENTIAL PATTERNS
  # ═══════════════════════════════════════════════════════════════
  
  PASSWORD_FIELD_PATTERN = ScrubPattern(
      name="password_field",
      pattern=re.compile(r'(?i)(password|passwd|pwd|secret)\s*[:=]\s*[\'"]?[^\s\'"]+[\'"]?'),
      replacement=r"\1=[PASSWORD_REDACTED]",
      category=PatternType.CREDENTIAL,
      description="Password fields in logs"
  )
  
  PRIVATE_KEY_PATTERN = ScrubPattern(
      name="private_key",
      pattern=re.compile(r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----'),
      replacement="[PRIVATE_KEY_REDACTED]",
      category=PatternType.CREDENTIAL,
      description="Private key headers"
  )
  
  CONNECTION_STRING_PATTERN = ScrubPattern(
      name="connection_string",
      pattern=re.compile(
          r'(?i)(postgresql|mysql|mongodb|redis)://[^:]+:[^@]+@[^\s]+'
      ),
      replacement=r"\1://[CREDENTIALS_REDACTED]@[HOST_REDACTED]",
      category=PatternType.CREDENTIAL,
      description="Database connection strings"
  )
  
  
  # ═══════════════════════════════════════════════════════════════
  # PATTERN REGISTRY
  # ═══════════════════════════════════════════════════════════════
  
  PATTERNS: Dict[str, ScrubPattern] = {
      # Identity
      "email": EMAIL_PATTERN,
      "phone": PHONE_PATTERN,
      "ssn": SSN_PATTERN,
      
      # Financial
      "credit_card": CREDIT_CARD_PATTERN,
      "credit_card_formatted": CREDIT_CARD_FORMATTED_PATTERN,
      
      # API Keys
      "openai_api_key": OPENAI_KEY_PATTERN,
      "stripe_api_key": STRIPE_KEY_PATTERN,
      "aws_access_key": AWS_ACCESS_KEY_PATTERN,
      "aws_secret_key": AWS_SECRET_KEY_PATTERN,
      "google_api_key": GOOGLE_API_KEY_PATTERN,
      "github_token": GITHUB_TOKEN_PATTERN,
      "slack_token": SLACK_TOKEN_PATTERN,
      
      # Auth Tokens
      "jwt": JWT_PATTERN,
      "bearer_token": BEARER_TOKEN_PATTERN,
      
      # Credentials
      "password_field": PASSWORD_FIELD_PATTERN,
      "private_key": PRIVATE_KEY_PATTERN,
      "connection_string": CONNECTION_STRING_PATTERN,
  }
  
  
  def get_patterns_by_category(category: PatternType) -> Dict[str, ScrubPattern]:
      """Get all patterns of a specific category."""
      return {
          name: pattern
          for name, pattern in PATTERNS.items()
          if pattern.category == category
      }
  EOF
  ```

- [ ] **2.1.2.3** Create `codewarden/scrubber/airlock.py`
  ```bash
  cat > codewarden/scrubber/airlock.py << 'EOF'
  """
  Airlock - Client-side PII scrubbing engine.
  
  The Airlock ensures no sensitive data leaves the user's server.
  All scrubbing happens locally before any transmission to CodeWarden.
  """
  
  import json
  from typing import Any, Dict, List, Optional, Set
  import structlog
  
  from codewarden.scrubber.patterns import PATTERNS, ScrubPattern
  
  logger = structlog.get_logger()
  
  
  class Airlock:
      """
      Client-side PII scrubbing engine.
      
      Usage:
          airlock = Airlock()
          safe_text = airlock.scrub("User john@email.com made payment")
          # Returns: "User [EMAIL_REDACTED] made payment"
      """
      
      def __init__(
          self,
          enabled_patterns: Optional[List[str]] = None,
          custom_patterns: Optional[Dict[str, ScrubPattern]] = None,
          fail_safe: bool = True
      ):
          """
          Initialize the Airlock.
          
          Args:
              enabled_patterns: List of pattern names to enable. 
                               If None, all patterns are enabled.
              custom_patterns: Additional custom patterns to use.
              fail_safe: If True, drop data that can't be safely scrubbed.
          """
          self.fail_safe = fail_safe
          self._patterns: Dict[str, ScrubPattern] = {}
          
          # Load enabled patterns
          if enabled_patterns is None:
              self._patterns = PATTERNS.copy()
          else:
              for name in enabled_patterns:
                  if name in PATTERNS:
                      self._patterns[name] = PATTERNS[name]
                  else:
                      logger.warning(f"Unknown pattern: {name}")
          
          # Add custom patterns
          if custom_patterns:
              self._patterns.update(custom_patterns)
          
          logger.debug(
              "Airlock initialized",
              patterns_count=len(self._patterns),
              patterns=list(self._patterns.keys())
          )
      
      def scrub(self, text: str) -> str:
          """
          Scrub PII from text.
          
          Args:
              text: The text to scrub.
              
          Returns:
              Scrubbed text safe for transmission.
          """
          if not text:
              return text
          
          result = text
          matches_found: Set[str] = set()
          
          for name, pattern in self._patterns.items():
              if pattern.pattern.search(result):
                  matches_found.add(name)
                  result = pattern.pattern.sub(pattern.replacement, result)
          
          if matches_found:
              logger.debug(
                  "PII scrubbed",
                  patterns_matched=list(matches_found),
                  original_length=len(text),
                  scrubbed_length=len(result)
              )
          
          return result
      
      def scrub_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
          """
          Recursively scrub all string values in a dictionary.
          
          Args:
              data: Dictionary to scrub.
              
          Returns:
              New dictionary with scrubbed values.
          """
          result = {}
          
          for key, value in data.items():
              if isinstance(value, str):
                  result[key] = self.scrub(value)
              elif isinstance(value, dict):
                  result[key] = self.scrub_dict(value)
              elif isinstance(value, list):
                  result[key] = self._scrub_list(value)
              else:
                  result[key] = value
          
          return result
      
      def _scrub_list(self, items: List[Any]) -> List[Any]:
          """Scrub items in a list."""
          result = []
          for item in items:
              if isinstance(item, str):
                  result.append(self.scrub(item))
              elif isinstance(item, dict):
                  result.append(self.scrub_dict(item))
              elif isinstance(item, list):
                  result.append(self._scrub_list(item))
              else:
                  result.append(item)
          return result
      
      def scrub_json(self, json_str: str) -> str:
          """
          Scrub PII from a JSON string.
          
          Args:
              json_str: JSON string to scrub.
              
          Returns:
              Scrubbed JSON string.
          """
          try:
              data = json.loads(json_str)
              scrubbed = self.scrub_dict(data)
              return json.dumps(scrubbed)
          except json.JSONDecodeError:
              # Not valid JSON, scrub as plain text
              return self.scrub(json_str)
      
      def is_safe(self, text: str) -> bool:
          """
          Check if text contains any detectable PII.
          
          Args:
              text: Text to check.
              
          Returns:
              True if no PII detected, False otherwise.
          """
          for pattern in self._patterns.values():
              if pattern.pattern.search(text):
                  return False
          return True
      
      def detect(self, text: str) -> List[str]:
          """
          Detect which patterns match in the text.
          
          Args:
              text: Text to analyze.
              
          Returns:
              List of pattern names that matched.
          """
          matches = []
          for name, pattern in self._patterns.items():
              if pattern.pattern.search(text):
                  matches.append(name)
          return matches
      
      def get_stats(self, text: str) -> Dict[str, Any]:
          """
          Get scrubbing statistics for a piece of text.
          
          Args:
              text: Text to analyze.
              
          Returns:
              Dictionary with statistics.
          """
          matches = self.detect(text)
          scrubbed = self.scrub(text)
          
          return {
              "original_length": len(text),
              "scrubbed_length": len(scrubbed),
              "patterns_matched": matches,
              "is_safe": len(matches) == 0,
              "redaction_count": len(matches)
          }
  EOF
  ```

- [ ] **2.1.2.4** Create Airlock tests
  ```bash
  cat > tests/unit/test_airlock.py << 'EOF'
  """Tests for the Airlock PII scrubber."""
  
  import pytest
  from codewarden.scrubber import Airlock
  
  
  class TestAirlock:
      """Test suite for Airlock."""
      
      @pytest.fixture
      def airlock(self):
          """Create a fresh Airlock instance."""
          return Airlock()
      
      # ─────────────────────────────────────────────────────────────
      # EMAIL TESTS
      # ─────────────────────────────────────────────────────────────
      
      def test_scrubs_email(self, airlock):
          text = "Contact john@example.com for support"
          result = airlock.scrub(text)
          assert "[EMAIL_REDACTED]" in result
          assert "john@example.com" not in result
      
      def test_scrubs_multiple_emails(self, airlock):
          text = "From alice@test.com to bob@test.org"
          result = airlock.scrub(text)
          assert result.count("[EMAIL_REDACTED]") == 2
      
      # ─────────────────────────────────────────────────────────────
      # CREDIT CARD TESTS
      # ─────────────────────────────────────────────────────────────
      
      def test_scrubs_credit_card(self, airlock):
          text = "Card: 4111111111111111"
          result = airlock.scrub(text)
          assert "[CC_REDACTED]" in result
          assert "4111111111111111" not in result
      
      def test_scrubs_formatted_credit_card(self, airlock):
          text = "Card: 4111-1111-1111-1111"
          result = airlock.scrub(text)
          assert "[CC_REDACTED]" in result
      
      # ─────────────────────────────────────────────────────────────
      # API KEY TESTS
      # ─────────────────────────────────────────────────────────────
      
      def test_scrubs_openai_key(self, airlock):
          text = "key = sk-1234567890abcdefghijklmnopqrstuvwxyz123456789012"
          result = airlock.scrub(text)
          assert "[OPENAI_KEY_REDACTED]" in result
      
      def test_scrubs_stripe_key(self, airlock):
          text = "STRIPE_KEY=sk_live_abcdefghijklmnopqrstuvwxyz"
          result = airlock.scrub(text)
          assert "[STRIPE_KEY_REDACTED]" in result
      
      def test_scrubs_aws_key(self, airlock):
          text = "AWS_KEY=AKIAIOSFODNN7EXAMPLE"
          result = airlock.scrub(text)
          assert "[AWS_KEY_REDACTED]" in result
      
      def test_scrubs_google_api_key(self, airlock):
          text = "GOOGLE_KEY=AIzaSyDaGmWKa4JsXZ-HjGw7ISLn_3namBGewQe"
          result = airlock.scrub(text)
          assert "[GOOGLE_KEY_REDACTED]" in result
      
      # ─────────────────────────────────────────────────────────────
      # JWT TESTS
      # ─────────────────────────────────────────────────────────────
      
      def test_scrubs_jwt(self, airlock):
          text = "token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
          result = airlock.scrub(text)
          assert "[JWT_REDACTED]" in result
      
      # ─────────────────────────────────────────────────────────────
      # PASSWORD TESTS
      # ─────────────────────────────────────────────────────────────
      
      def test_scrubs_password_field(self, airlock):
          text = "password=mysecretpassword123"
          result = airlock.scrub(text)
          assert "[PASSWORD_REDACTED]" in result
          assert "mysecretpassword123" not in result
      
      # ─────────────────────────────────────────────────────────────
      # DICTIONARY TESTS
      # ─────────────────────────────────────────────────────────────
      
      def test_scrubs_dict(self, airlock):
          data = {
              "user": "john@example.com",
              "card": "4111111111111111",
              "nested": {
                  "api_key": "sk_live_abcdefghijklmnopqrstuvwxyz"
              }
          }
          result = airlock.scrub_dict(data)
          assert "[EMAIL_REDACTED]" in result["user"]
          assert "[CC_REDACTED]" in result["card"]
          assert "[STRIPE_KEY_REDACTED]" in result["nested"]["api_key"]
      
      # ─────────────────────────────────────────────────────────────
      # SAFETY TESTS
      # ─────────────────────────────────────────────────────────────
      
      def test_is_safe_with_clean_text(self, airlock):
          assert airlock.is_safe("Normal log message")
      
      def test_is_safe_with_pii(self, airlock):
          assert not airlock.is_safe("Email: john@example.com")
      
      def test_preserves_safe_text(self, airlock):
          text = "Normal log message without PII"
          assert airlock.scrub(text) == text
      
      # ─────────────────────────────────────────────────────────────
      # DETECTION TESTS
      # ─────────────────────────────────────────────────────────────
      
      def test_detect_multiple_patterns(self, airlock):
          text = "john@example.com used card 4111111111111111"
          matches = airlock.detect(text)
          assert "email" in matches
          assert "credit_card" in matches
  EOF
  ```

**Testing:**
- [ ] Run `cd packages/sdk-python && poetry run pytest tests/unit/test_airlock.py -v`
- [ ] All tests pass

---

### Task 2.1.3: Implement FastAPI Middleware

**Sub-tasks:**

- [ ] **2.1.3.1** Create `codewarden/middleware/__init__.py`
  ```bash
  cat > codewarden/middleware/__init__.py << 'EOF'
  """Framework middleware for CodeWarden."""
  
  from codewarden.middleware.fastapi import CodeWardenMiddleware
  
  __all__ = ["CodeWardenMiddleware"]
  EOF
  ```

- [ ] **2.1.3.2** Create `codewarden/middleware/fastapi.py`
  ```bash
  cat > codewarden/middleware/fastapi.py << 'EOF'
  """FastAPI middleware for CodeWarden."""
  
  import time
  import traceback
  import uuid
  from typing import Callable, Optional
  
  from starlette.middleware.base import BaseHTTPMiddleware
  from starlette.requests import Request
  from starlette.responses import Response
  from starlette.types import ASGIApp
  import structlog
  
  from codewarden.config import CodeWardenConfig, get_config
  from codewarden.scrubber import Airlock
  from codewarden.transport import TransportClient
  
  logger = structlog.get_logger()
  
  
  class CodeWardenMiddleware(BaseHTTPMiddleware):
      """
      FastAPI/Starlette middleware for CodeWarden.
      
      Intercepts all HTTP requests and:
      1. Generates trace IDs for request correlation
      2. Measures request latency
      3. Catches unhandled exceptions
      4. Scrubs and reports errors to CodeWarden
      """
      
      def __init__(
          self,
          app: ASGIApp,
          config: Optional[CodeWardenConfig] = None,
          airlock: Optional[Airlock] = None,
          transport: Optional[TransportClient] = None
      ):
          super().__init__(app)
          self.config = config or get_config()
          self.airlock = airlock or Airlock()
          self.transport = transport or TransportClient(self.config)
          
          logger.info(
              "CodeWarden middleware initialized",
              enabled=self.config.enabled,
              scrub_pii=self.config.scrub_pii
          )
      
      async def dispatch(
          self,
          request: Request,
          call_next: Callable
      ) -> Response:
          """Process each request."""
          
          # Skip if disabled
          if not self.config.enabled:
              return await call_next(request)
          
          # Generate trace ID
          trace_id = self._generate_trace_id()
          request.state.trace_id = trace_id
          
          # Record start time
          start_time = time.perf_counter()
          
          try:
              # Process request
              response = await call_next(request)
              
              # Calculate duration
              duration_ms = (time.perf_counter() - start_time) * 1000
              
              # Log request (if enabled)
              if self.config.capture_requests:
                  await self._log_request(
                      trace_id=trace_id,
                      request=request,
                      response=response,
                      duration_ms=duration_ms
                  )
              
              # Add trace ID header
              response.headers["X-CodeWarden-Trace-ID"] = trace_id
              
              return response
              
          except Exception as exc:
              # Calculate duration
              duration_ms = (time.perf_counter() - start_time) * 1000
              
              # Report error
              if self.config.capture_errors:
                  await self._report_error(
                      trace_id=trace_id,
                      request=request,
                      error=exc,
                      duration_ms=duration_ms
                  )
              
              # Re-raise to let FastAPI handle the response
              raise
      
      def _generate_trace_id(self) -> str:
          """Generate a unique trace ID."""
          return f"cw-{uuid.uuid4().hex[:16]}"
      
      async def _log_request(
          self,
          trace_id: str,
          request: Request,
          response: Response,
          duration_ms: float
      ) -> None:
          """Log request metadata."""
          
          payload = {
              "trace_id": trace_id,
              "method": request.method,
              "path": str(request.url.path),
              "query": str(request.url.query) if request.url.query else None,
              "status_code": response.status_code,
              "duration_ms": round(duration_ms, 2),
              "client_ip": self._get_client_ip(request),
              "user_agent": request.headers.get("user-agent"),
          }
          
          # Scrub if enabled
          if self.config.scrub_pii:
              payload = self.airlock.scrub_dict(payload)
          
          await self.transport.send_telemetry(
              event_type="request",
              severity="info",
              payload=payload
          )
      
      async def _report_error(
          self,
          trace_id: str,
          request: Request,
          error: Exception,
          duration_ms: float
      ) -> None:
          """Report an error to CodeWarden."""
          
          # Get stack trace
          tb = traceback.format_exc()
          
          # Scrub the trace
          if self.config.scrub_pii:
              tb = self.airlock.scrub(tb)
          
          payload = {
              "trace_id": trace_id,
              "error_type": type(error).__name__,
              "error_message": str(error),
              "trace_scrubbed": tb,
              "request": {
                  "method": request.method,
                  "path": str(request.url.path),
                  "query": str(request.url.query) if request.url.query else None,
              },
              "duration_ms": round(duration_ms, 2),
          }
          
          # Scrub payload
          if self.config.scrub_pii:
              payload = self.airlock.scrub_dict(payload)
          
          await self.transport.send_telemetry(
              event_type="crash",
              severity="critical",
              payload=payload
          )
          
          logger.error(
              "Error captured",
              trace_id=trace_id,
              error_type=type(error).__name__,
              path=request.url.path
          )
      
      def _get_client_ip(self, request: Request) -> Optional[str]:
          """Extract client IP from request."""
          # Check X-Forwarded-For header first (for proxied requests)
          forwarded = request.headers.get("x-forwarded-for")
          if forwarded:
              return forwarded.split(",")[0].strip()
          
          # Fall back to direct client
          if request.client:
              return request.client.host
          
          return None
  EOF
  ```

- [ ] **2.1.3.3** Create `codewarden/transport/__init__.py`
  ```bash
  mkdir -p codewarden/transport
  
  cat > codewarden/transport/__init__.py << 'EOF'
  """Transport layer for CodeWarden."""
  
  from codewarden.transport.client import TransportClient
  
  __all__ = ["TransportClient"]
  EOF
  ```

- [ ] **2.1.3.4** Create `codewarden/transport/client.py`
  ```bash
  cat > codewarden/transport/client.py << 'EOF'
  """HTTP transport client for CodeWarden API."""
  
  import asyncio
  from datetime import datetime, timezone
  from typing import Any, Dict, Optional
  
  import httpx
  from tenacity import retry, stop_after_attempt, wait_exponential
  import structlog
  
  from codewarden.config import CodeWardenConfig
  
  logger = structlog.get_logger()
  
  
  class TransportClient:
      """
      HTTP client for sending data to CodeWarden API.
      
      Features:
      - Async HTTP with httpx
      - Automatic retries with exponential backoff
      - Request timeout handling
      - Graceful degradation on failure
      """
      
      def __init__(self, config: CodeWardenConfig):
          self.config = config
          self._client: Optional[httpx.AsyncClient] = None
          self._queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
          self._worker_task: Optional[asyncio.Task] = None
      
      async def _get_client(self) -> httpx.AsyncClient:
          """Get or create the HTTP client."""
          if self._client is None or self._client.is_closed:
              self._client = httpx.AsyncClient(
                  base_url=self.config.api_url,
                  timeout=self.config.request_timeout,
                  headers={
                      "Content-Type": "application/json",
                      "User-Agent": "codewarden-python/0.1.0",
                  }
              )
          return self._client
      
      async def close(self) -> None:
          """Close the HTTP client."""
          if self._client:
              await self._client.aclose()
              self._client = None
      
      @retry(
          stop=stop_after_attempt(3),
          wait=wait_exponential(multiplier=1, min=1, max=10),
          reraise=True
      )
      async def _send_request(
          self,
          endpoint: str,
          payload: Dict[str, Any]
      ) -> Dict[str, Any]:
          """Send a request with retry logic."""
          client = await self._get_client()
          
          # Add API key if available
          headers = {}
          if self.config.api_key:
              headers["Authorization"] = f"Bearer {self.config.api_key.get_secret_value()}"
          
          response = await client.post(
              endpoint,
              json=payload,
              headers=headers
          )
          response.raise_for_status()
          return response.json()
      
      async def send_telemetry(
          self,
          event_type: str,
          severity: str,
          payload: Dict[str, Any]
      ) -> Optional[Dict[str, Any]]:
          """
          Send telemetry data to CodeWarden.
          
          Args:
              event_type: Type of event (crash, request, etc.)
              severity: Severity level (critical, warning, info)
              payload: Event payload
              
          Returns:
              API response or None if failed
          """
          if not self.config.enabled:
              return None
          
          if not self.config.api_key:
              logger.debug("No API key configured, skipping telemetry")
              return None
          
          data = {
              "source": "backend-python",
              "type": event_type,
              "severity": severity,
              "environment": self.config.environment,
              "payload": payload,
              "timestamp": datetime.now(timezone.utc).isoformat()
          }
          
          try:
              result = await self._send_request("/v1/telemetry", data)
              logger.debug(
                  "Telemetry sent",
                  event_type=event_type,
                  event_id=result.get("id")
              )
              return result
          except httpx.HTTPStatusError as e:
              logger.warning(
                  "Failed to send telemetry",
                  status_code=e.response.status_code,
                  error=str(e)
              )
              return None
          except Exception as e:
              logger.warning(
                  "Failed to send telemetry",
                  error=str(e)
              )
              return None
      
      async def send_evidence(
          self,
          event_type: str,
          data: Dict[str, Any]
      ) -> Optional[Dict[str, Any]]:
          """
          Send evidence data for compliance logging.
          
          Args:
              event_type: Type of evidence (AUDIT_DEPLOY, AUDIT_SCAN, etc.)
              data: Evidence payload
              
          Returns:
              API response or None if failed
          """
          if not self.config.enabled or not self.config.evidence_logging:
              return None
          
          payload = {
              "type": event_type,
              "data": data,
              "timestamp": datetime.now(timezone.utc).isoformat()
          }
          
          try:
              return await self._send_request("/v1/evidence", payload)
          except Exception as e:
              logger.warning(
                  "Failed to send evidence",
                  event_type=event_type,
                  error=str(e)
              )
              return None
  EOF
  ```

**Testing:**
- [ ] Create middleware integration test
- [ ] Run tests: `poetry run pytest -v`

---

### Task 2.1.4: Implement Core CodeWarden Class

**Sub-tasks:**

- [ ] **2.1.4.1** Create `codewarden/core.py`
  ```bash
  cat > codewarden/core.py << 'EOF'
  """
  Core CodeWarden class - main entry point.
  
  Usage:
      from fastapi import FastAPI
      from codewarden import CodeWarden
      
      app = FastAPI()
      warden = CodeWarden(app)
  """
  
  import asyncio
  import platform
  import sys
  from typing import Any, Dict, Optional, TYPE_CHECKING
  
  import structlog
  
  from codewarden.config import CodeWardenConfig, get_config, set_config
  from codewarden.middleware import CodeWardenMiddleware
  from codewarden.scrubber import Airlock
  from codewarden.transport import TransportClient
  from codewarden.scanner import DependencyScanner, SecretScanner
  from codewarden.evidence import EvidenceCollector
  
  if TYPE_CHECKING:
      from fastapi import FastAPI
  
  logger = structlog.get_logger()
  
  
  class CodeWarden:
      """
      Main CodeWarden security agent.
      
      Usage:
          from fastapi import FastAPI
          from codewarden import CodeWarden
          
          app = FastAPI()
          warden = CodeWarden(app)
          
          # That's it! CodeWarden is now watching your app.
      """
      
      def __init__(
          self,
          app: Optional["FastAPI"] = None,
          *,
          api_key: Optional[str] = None,
          api_url: Optional[str] = None,
          scrub_pii: bool = True,
          scan_on_startup: bool = True,
          capture_errors: bool = True,
          evidence_logging: bool = True,
          environment: Optional[str] = None,
          config: Optional[CodeWardenConfig] = None
      ):
          """
          Initialize CodeWarden.
          
          Args:
              app: FastAPI application to instrument
              api_key: Your CodeWarden API key (or set CODEWARDEN_API_KEY)
              api_url: API endpoint (default: https://api.codewarden.io)
              scrub_pii: Enable PII scrubbing before transmission
              scan_on_startup: Run vulnerability scan on startup
              capture_errors: Capture and report errors
              evidence_logging: Enable compliance evidence logging
              environment: Environment name (production, staging, development)
              config: Full configuration object (overrides other params)
          """
          # Build configuration
          if config:
              self.config = config
          else:
              config_kwargs: Dict[str, Any] = {}
              if api_key:
                  config_kwargs["api_key"] = api_key
              if api_url:
                  config_kwargs["api_url"] = api_url
              if environment:
                  config_kwargs["environment"] = environment
              
              config_kwargs["scrub_pii"] = scrub_pii
              config_kwargs["scan_on_startup"] = scan_on_startup
              config_kwargs["capture_errors"] = capture_errors
              config_kwargs["evidence_logging"] = evidence_logging
              
              self.config = CodeWardenConfig(**config_kwargs)
          
          # Set global config
          set_config(self.config)
          
          # Initialize components
          self.airlock = Airlock()
          self.transport = TransportClient(self.config)
          self.evidence = EvidenceCollector(self.transport)
          
          # Attach to app if provided
          if app:
              self.instrument(app)
          
          # Run startup tasks
          if self.config.enabled:
              asyncio.create_task(self._startup())
          
          logger.info(
              "CodeWarden initialized",
              enabled=self.config.enabled,
              environment=self.config.environment,
              scrub_pii=self.config.scrub_pii,
              scan_on_startup=self.config.scan_on_startup
          )
      
      def instrument(self, app: "FastAPI") -> None:
          """
          Attach CodeWarden to a FastAPI application.
          
          Args:
              app: FastAPI application to instrument
          """
          app.add_middleware(
              CodeWardenMiddleware,
              config=self.config,
              airlock=self.airlock,
              transport=self.transport
          )
          
          # Store reference on app
          app.state.codewarden = self
          
          logger.info("CodeWarden attached to FastAPI app")
      
      async def _startup(self) -> None:
          """Run startup tasks."""
          # Log deployment event
          if self.config.evidence_logging:
              await self.evidence.log_deployment(
                  version=self._get_app_version(),
                  runtime=f"python{sys.version_info.major}.{sys.version_info.minor}"
              )
          
          # Run security scan
          if self.config.scan_on_startup:
              await self._run_startup_scan()
      
      async def _run_startup_scan(self) -> None:
          """Run security scans on startup."""
          # Dependency scan
          try:
              scanner = DependencyScanner()
              vulns = scanner.scan()
              
              await self.evidence.log_security_scan(
                  tool_name="pip-audit",
                  status="FAIL" if vulns else "PASS",
                  issue_count=len(vulns),
                  details={"vulnerabilities": [v.to_dict() for v in vulns]}
              )
              
              if vulns:
                  logger.warning(
                      "Vulnerabilities found",
                      count=len(vulns),
                      packages=[v.package for v in vulns]
                  )
          except Exception as e:
              logger.warning(f"Dependency scan failed: {e}")
          
          # Secret scan
          try:
              scanner = SecretScanner()
              secrets = scanner.scan_environment()
              
              if secrets:
                  await self.evidence.log_security_scan(
                      tool_name="secret-scanner",
                      status="FAIL",
                      issue_count=len(secrets),
                      details={"secrets_in_env": [s["env_var"] for s in secrets]}
                  )
                  
                  logger.warning(
                      "Secrets detected in environment",
                      count=len(secrets),
                      variables=[s["env_var"] for s in secrets]
                  )
          except Exception as e:
              logger.warning(f"Secret scan failed: {e}")
      
      def _get_app_version(self) -> str:
          """Get the application version."""
          # Try to get from common version files
          import importlib.metadata
          
          try:
              # Try to get from the main package
              return importlib.metadata.version("codewarden")
          except importlib.metadata.PackageNotFoundError:
              pass
          
          return "unknown"
      
      async def report_error(
          self,
          error: Exception,
          context: Optional[Dict[str, Any]] = None
      ) -> None:
          """
          Manually report an error to CodeWarden.
          
          Args:
              error: The exception to report
              context: Additional context to include
          """
          import traceback
          
          tb = traceback.format_exc()
          
          if self.config.scrub_pii:
              tb = self.airlock.scrub(tb)
              if context:
                  context = self.airlock.scrub_dict(context)
          
          await self.transport.send_telemetry(
              event_type="crash",
              severity="critical",
              payload={
                  "error_type": type(error).__name__,
                  "error_message": str(error),
                  "trace_scrubbed": tb,
                  "context": context or {}
              }
          )
      
      async def log_event(
          self,
          event_type: str,
          data: Dict[str, Any],
          severity: str = "info"
      ) -> None:
          """
          Log a custom event to CodeWarden.
          
          Args:
              event_type: Type of event
              data: Event data
              severity: Severity level (info, warning, critical)
          """
          if self.config.scrub_pii:
              data = self.airlock.scrub_dict(data)
          
          await self.transport.send_telemetry(
              event_type=event_type,
              severity=severity,
              payload=data
          )
      
      async def close(self) -> None:
          """Cleanup resources."""
          await self.transport.close()
  EOF
  ```

- [ ] **2.1.4.2** Create scanner modules
  ```bash
  mkdir -p codewarden/scanner
  
  cat > codewarden/scanner/__init__.py << 'EOF'
  """Security scanning modules."""
  
  from codewarden.scanner.dependencies import DependencyScanner, Vulnerability
  from codewarden.scanner.secrets import SecretScanner
  
  __all__ = ["DependencyScanner", "Vulnerability", "SecretScanner"]
  EOF
  ```

- [ ] **2.1.4.3** Create `codewarden/scanner/dependencies.py`
  ```bash
  cat > codewarden/scanner/dependencies.py << 'EOF'
  """Dependency vulnerability scanning using pip-audit."""
  
  import subprocess
  import json
  from dataclasses import dataclass
  from typing import List, Optional
  import structlog
  
  logger = structlog.get_logger()
  
  
  @dataclass
  class Vulnerability:
      """A detected vulnerability."""
      package: str
      installed_version: str
      vulnerability_id: str
      severity: str
      fix_version: Optional[str]
      description: str
      
      def to_dict(self) -> dict:
          return {
              "package": self.package,
              "installed_version": self.installed_version,
              "vulnerability_id": self.vulnerability_id,
              "severity": self.severity,
              "fix_version": self.fix_version,
              "description": self.description
          }
  
  
  class DependencyScanner:
      """Scans Python dependencies for known vulnerabilities."""
      
      def scan(self) -> List[Vulnerability]:
          """
          Run pip-audit on the current environment.
          
          Returns:
              List of detected vulnerabilities.
          """
          try:
              result = subprocess.run(
                  ["pip-audit", "--format", "json", "--progress-spinner", "off"],
                  capture_output=True,
                  text=True,
                  timeout=120
              )
              
              # pip-audit returns non-zero if vulnerabilities found
              if not result.stdout:
                  return []
              
              data = json.loads(result.stdout)
              vulnerabilities = []
              
              for dep in data.get("dependencies", []):
                  for vuln in dep.get("vulns", []):
                      vulnerabilities.append(Vulnerability(
                          package=dep["name"],
                          installed_version=dep["version"],
                          vulnerability_id=vuln["id"],
                          severity=self._map_severity(vuln),
                          fix_version=vuln.get("fix_versions", [None])[0],
                          description=vuln.get("description", "")[:500]
                      ))
              
              return vulnerabilities
              
          except FileNotFoundError:
              logger.warning("pip-audit not installed, skipping dependency scan")
              return []
          except subprocess.TimeoutExpired:
              logger.warning("pip-audit timed out")
              return []
          except json.JSONDecodeError as e:
              logger.warning(f"Failed to parse pip-audit output: {e}")
              return []
          except Exception as e:
              logger.warning(f"Dependency scan failed: {e}")
              return []
      
      def _map_severity(self, vuln: dict) -> str:
          """Map vulnerability to severity level."""
          # pip-audit doesn't always include severity
          # We can infer from the ID or description
          vuln_id = vuln.get("id", "").upper()
          
          if "CRITICAL" in vuln_id or "CVE" in vuln_id:
              return "high"
          return "medium"
      
      def get_fix_commands(self, vulnerabilities: List[Vulnerability]) -> List[str]:
          """Generate commands to fix vulnerabilities."""
          commands = []
          for vuln in vulnerabilities:
              if vuln.fix_version:
                  commands.append(f"pip install {vuln.package}>={vuln.fix_version}")
          return commands
  EOF
  ```

- [ ] **2.1.4.4** Create `codewarden/scanner/secrets.py`
  ```bash
  cat > codewarden/scanner/secrets.py << 'EOF'
  """Secret detection in environment and code."""
  
  import os
  from typing import List, Dict, Any
  import structlog
  
  from codewarden.scrubber.patterns import PATTERNS, PatternType
  
  logger = structlog.get_logger()
  
  
  class SecretScanner:
      """Detects secrets in environment variables and files."""
      
      def __init__(self):
          # Get API key patterns
          self.patterns = {
              name: pattern
              for name, pattern in PATTERNS.items()
              if pattern.category == PatternType.API_KEY
          }
      
      def scan_environment(self) -> List[Dict[str, Any]]:
          """
          Scan environment variables for exposed secrets.
          
          Returns:
              List of detected secrets (with values redacted).
          """
          findings = []
          
          for key, value in os.environ.items():
              for pattern_name, pattern in self.patterns.items():
                  if pattern.pattern.search(value):
                      findings.append({
                          "env_var": key,
                          "pattern": pattern_name,
                          "severity": "high",
                          "recommendation": f"Move {key} to a secrets manager"
                      })
                      break  # One finding per env var
          
          if findings:
              logger.warning(
                  "Secrets detected in environment",
                  count=len(findings)
              )
          
          return findings
      
      def scan_text(self, text: str) -> List[Dict[str, Any]]:
          """
          Scan text for secrets.
          
          Args:
              text: Text to scan
              
          Returns:
              List of detected secrets.
          """
          findings = []
          
          for pattern_name, pattern in self.patterns.items():
              matches = pattern.pattern.finditer(text)
              for match in matches:
                  findings.append({
                      "pattern": pattern_name,
                      "position": match.start(),
                      "severity": "high"
                  })
          
          return findings
  EOF
  ```

- [ ] **2.1.4.5** Create evidence module
  ```bash
  mkdir -p codewarden/evidence
  
  cat > codewarden/evidence/__init__.py << 'EOF'
  """Evidence collection for SOC 2 compliance."""
  
  from codewarden.evidence.collector import EvidenceCollector
  
  __all__ = ["EvidenceCollector"]
  EOF
  
  cat > codewarden/evidence/collector.py << 'EOF'
  """Evidence collector for compliance logging."""
  
  import platform
  from datetime import datetime, timezone
  from typing import Any, Dict, Optional
  import structlog
  
  from codewarden.transport import TransportClient
  
  logger = structlog.get_logger()
  
  
  class EvidenceCollector:
      """
      Collects compliance evidence for SOC 2 audits.
      
      Records:
      - Deployment events
      - Security scan results
      - Access events
      - Configuration changes
      """
      
      def __init__(self, transport: TransportClient):
          self.transport = transport
      
      async def log_deployment(
          self,
          version: str,
          commit_hash: Optional[str] = None,
          deployer: str = "system",
          runtime: Optional[str] = None
      ) -> None:
          """
          Log a deployment event.
          
          Auditors need: "Who deployed what, when?"
          """
          await self.transport.send_evidence(
              event_type="AUDIT_DEPLOY",
              data={
                  "version": version,
                  "commit_hash": commit_hash,
                  "deployer": deployer,
                  "runtime": runtime or f"python{platform.python_version()}",
                  "platform": platform.platform(),
                  "timestamp": datetime.now(timezone.utc).isoformat()
              }
          )
          
          logger.info(
              "Deployment logged",
              version=version,
              deployer=deployer
          )
      
      async def log_security_scan(
          self,
          tool_name: str,
          status: str,
          issue_count: int,
          details: Optional[Dict[str, Any]] = None
      ) -> None:
          """
          Log a security scan result.
          
          Auditors need: "Did you check for vulnerabilities?"
          """
          await self.transport.send_evidence(
              event_type="AUDIT_SCAN",
              data={
                  "tool": tool_name,
                  "status": status,
                  "issue_count": issue_count,
                  "details": details or {},
                  "timestamp": datetime.now(timezone.utc).isoformat()
              }
          )
          
          logger.info(
              "Security scan logged",
              tool=tool_name,
              status=status,
              issues=issue_count
          )
      
      async def log_access_event(
          self,
          user_id: str,
          action: str,
          resource: str,
          ip_address: Optional[str] = None,
          success: bool = True
      ) -> None:
          """
          Log an access/authentication event.
          
          Auditors need: "Who accessed what?"
          """
          await self.transport.send_evidence(
              event_type="AUDIT_ACCESS",
              data={
                  "user_id": user_id,
                  "action": action,
                  "resource": resource,
                  "ip_address": ip_address,
                  "success": success,
                  "timestamp": datetime.now(timezone.utc).isoformat()
              }
          )
  EOF
  ```

**Testing:**
- [ ] Run full test suite: `poetry run pytest -v`
- [ ] Run type checking: `poetry run mypy codewarden`
- [ ] Run linting: `poetry run ruff check codewarden`

---

## Story 2.2: API Development

### Task 2.2.1: Initialize API Package

**Sub-tasks:**

- [ ] **2.2.1.1** Create API package structure
  ```bash
  cd packages/api
  
  # Initialize with Poetry
  poetry init --name codewarden-api --description "CodeWarden API Server" --author "Your Name <you@email.com>" --python "^3.11" --no-interaction
  
  # Create directories
  mkdir -p api/{routes,workers,brain,services,models}
  mkdir -p tests/{unit,integration}
  mkdir -p alembic/versions
  ```

- [ ] **2.2.1.2** Create `pyproject.toml`
  ```bash
  cat > pyproject.toml << 'EOF'
  [tool.poetry]
  name = "codewarden-api"
  version = "0.1.0"
  description = "CodeWarden API Server"
  authors = ["CodeWarden <hello@codewarden.io>"]
  
  [tool.poetry.dependencies]
  python = "^3.11"
  fastapi = "^0.109.0"
  uvicorn = {extras = ["standard"], version = "^0.27.0"}
  pydantic = "^2.5.0"
  pydantic-settings = "^2.1.0"
  sqlalchemy = "^2.0.0"
  alembic = "^1.13.0"
  asyncpg = "^0.29.0"
  redis = "^5.0.0"
  arq = "^0.25.0"
  httpx = "^0.27.0"
  litellm = "^1.20.0"
  structlog = "^24.1.0"
  tenacity = "^8.2.0"
  python-multipart = "^0.0.9"
  bcrypt = "^4.1.0"
  resend = "^0.7.0"
  python-telegram-bot = "^20.7"
  boto3 = "^1.34.0"
  
  [tool.poetry.group.dev.dependencies]
  pytest = "^8.0.0"
  pytest-cov = "^4.1.0"
  pytest-asyncio = "^0.23.0"
  httpx = "^0.27.0"
  ruff = "^0.2.0"
  mypy = "^1.8.0"
  
  [tool.ruff]
  line-length = 100
  target-version = "py311"
  
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  asyncio_mode = "auto"
  
  [build-system]
  requires = ["poetry-core"]
  build-backend = "poetry.core.masonry.api"
  EOF
  ```

- [ ] **2.2.1.3** Install dependencies
  ```bash
  poetry install
  ```

**Testing:**
- [ ] Run `poetry check` → No errors

---

### Task 2.2.2: Create FastAPI Application

**Sub-tasks:**

- [ ] **2.2.2.1** Create `api/__init__.py`
  ```bash
  cat > api/__init__.py << 'EOF'
  """CodeWarden API Server."""
  
  __version__ = "0.1.0"
  EOF
  ```

- [ ] **2.2.2.2** Create `api/config.py`
  ```bash
  cat > api/config.py << 'EOF'
  """API configuration."""
  
  from typing import Optional
  from pydantic_settings import BaseSettings
  from pydantic import Field, SecretStr
  
  
  class Settings(BaseSettings):
      """Application settings."""
      
      # Environment
      environment: str = Field(default="development")
      debug: bool = Field(default=False)
      log_level: str = Field(default="info")
      
      # Server
      host: str = Field(default="0.0.0.0")
      port: int = Field(default=8000)
      workers: int = Field(default=1)
      
      # Database
      database_url: str = Field(default="postgresql://postgres:postgres@localhost:5432/postgres")
      
      # Redis
      redis_url: str = Field(default="redis://localhost:6379")
      
      # OpenObserve
      openobserve_url: str = Field(default="http://localhost:5080")
      openobserve_org: str = Field(default="default")
      openobserve_user: str = Field(default="admin@codewarden.local")
      openobserve_password: SecretStr = Field(default="admin123")
      
      # AI Providers
      google_api_key: Optional[SecretStr] = None
      anthropic_api_key: Optional[SecretStr] = None
      openai_api_key: Optional[SecretStr] = None
      
      # Notifications
      resend_api_key: Optional[SecretStr] = None
      telegram_bot_token: Optional[SecretStr] = None
      
      # Storage
      r2_access_key_id: Optional[str] = None
      r2_secret_access_key: Optional[SecretStr] = None
      r2_bucket: str = Field(default="codewarden-evidence")
      r2_endpoint: Optional[str] = None
      
      model_config = {
          "env_file": ".env",
          "extra": "ignore"
      }
  
  
  settings = Settings()
  EOF
  ```

- [ ] **2.2.2.3** Create `api/main.py`
  ```bash
  cat > api/main.py << 'EOF'
  """FastAPI application entry point."""
  
  from contextlib import asynccontextmanager
  from typing import AsyncGenerator
  
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  import structlog
  
  from api.config import settings
  from api.routes import telemetry, evidence, health, pairing
  from api.services.database import init_db, close_db
  from api.services.redis import init_redis, close_redis
  
  # Configure logging
  structlog.configure(
      processors=[
          structlog.stdlib.filter_by_level,
          structlog.processors.TimeStamper(fmt="iso"),
          structlog.processors.JSONRenderer()
      ],
      wrapper_class=structlog.stdlib.BoundLogger,
      context_class=dict,
      logger_factory=structlog.stdlib.LoggerFactory(),
  )
  
  logger = structlog.get_logger()
  
  
  @asynccontextmanager
  async def lifespan(app: FastAPI) -> AsyncGenerator:
      """Application lifespan handler."""
      # Startup
      logger.info("Starting CodeWarden API", environment=settings.environment)
      await init_db()
      await init_redis()
      
      yield
      
      # Shutdown
      logger.info("Shutting down CodeWarden API")
      await close_db()
      await close_redis()
  
  
  # Create application
  app = FastAPI(
      title="CodeWarden API",
      description="Security monitoring for solopreneurs",
      version="0.1.0",
      docs_url="/docs" if settings.debug else None,
      redoc_url="/redoc" if settings.debug else None,
      lifespan=lifespan
  )
  
  # CORS middleware
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[
          "http://localhost:3000",
          "https://app.codewarden.io",
      ],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  
  # Include routers
  app.include_router(health.router, tags=["Health"])
  app.include_router(telemetry.router, prefix="/v1", tags=["Telemetry"])
  app.include_router(evidence.router, prefix="/v1", tags=["Evidence"])
  app.include_router(pairing.router, prefix="/v1", tags=["Pairing"])
  
  
  @app.get("/")
  async def root():
      """Root endpoint."""
      return {
          "name": "CodeWarden API",
          "version": "0.1.0",
          "status": "running"
      }
  EOF
  ```

**Continue with remaining API routes and services in subsequent tasks...**

---

## Phase 2 Testing Checklist

### Python SDK Tests
- [ ] Airlock unit tests pass
- [ ] Pattern detection tests pass
- [ ] Middleware integration tests pass
- [ ] Transport client tests pass
- [ ] Scanner tests pass
- [ ] Full SDK test suite: `poetry run pytest --cov`

### API Tests
- [ ] Health endpoint returns 200
- [ ] Telemetry endpoint accepts valid payloads
- [ ] Evidence endpoint logs events
- [ ] Pairing endpoints work correctly
- [ ] Database migrations run successfully
- [ ] Worker processes jobs correctly

### Integration Tests
- [ ] SDK can connect to local API
- [ ] Errors are captured and sent
- [ ] PII is scrubbed correctly
- [ ] Evidence is logged to database

---

## Next Steps

Proceed to **Part 3: Frontend, Integration & Launch** which covers:
- Dashboard development with Next.js
- JavaScript SDK implementation
- End-to-end integration testing
- Launch preparation and deployment

---

**Document Control:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2026 | Engineering | Initial release |
