# CodeWarden Technical PRD

**Document Version:** 1.0  
**Status:** Approved for Development  
**Last Updated:** January 2026  
**Owner:** Engineering Team

---

## 1. Technical Overview

### 1.1 System Architecture

CodeWarden is built on a **4-Layer "Hub & Spoke" Architecture** designed for reliability, model-agnosticism, and acquisition-readiness.

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 1: THE EDGE                            │
│              (User's Infrastructure - Client-Side)              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  codewarden-py   │    │  codewarden-js   │                   │
│  │  (Python Agent)  │    │  (Node.js Agent) │                   │
│  │                  │    │                  │                   │
│  │  • Middleware    │    │  • Instrumentation│                  │
│  │  • Scrubber      │    │  • Console Guard │                   │
│  │  • Vuln Scanner  │    │  • Network Spy   │                   │
│  │  • Evidence Log  │    │  • Error Boundary│                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                             │
│           └───────────┬───────────┘                             │
│                       │ HTTPS (Scrubbed Data Only)              │
└───────────────────────┼─────────────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────────────┐
│                       ▼                                         │
│                 LAYER 2: THE GATEWAY                            │
│                   (Our API Server)                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐       │
│  │              FastAPI Ingestion Service               │       │
│  │                                                      │       │
│  │  POST /v1/telemetry    - Error/Log ingestion        │       │
│  │  POST /v1/evidence     - Compliance events          │       │
│  │  GET  /v1/health       - SDK health check           │       │
│  └──────────────────────────┬───────────────────────────┘       │
│                             │                                   │
│  ┌──────────────────────────▼───────────────────────────┐       │
│  │              Redis + ARQ Job Queue                   │       │
│  │         (Async processing, not blocking)             │       │
│  └──────────────────────────┬───────────────────────────┘       │
└─────────────────────────────┼───────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                             ▼                                   │
│                    LAYER 3: THE BRAIN                           │
│                    (AI Analysis Engine)                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐       │
│  │                    LiteLLM Router                    │       │
│  │                                                      │       │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │       │
│  │  │   Gemini    │ │   Claude    │ │   GPT-4o    │    │       │
│  │  │   Flash     │ │   Sonnet    │ │   Mini      │    │       │
│  │  │   (Fast)    │ │   (Smart)   │ │  (Fallback) │    │       │
│  │  └─────────────┘ └─────────────┘ └─────────────┘    │       │
│  │                                                      │       │
│  │  • Automatic failover between providers              │       │
│  │  • Consensus Check for critical alerts               │       │
│  │  • Cost optimization (cheap for simple, smart for    │       │
│  │    complex)                                          │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                             ▼                                   │
│                    LAYER 4: THE VAULT                           │
│                    (Storage & Persistence)                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   OpenObserve   │  │    Supabase     │  │   S3 / R2       │  │
│  │   (Log Store)   │  │   (Metadata)    │  │ (Evidence PDFs) │  │
│  │                 │  │                 │  │                 │  │
│  │  • Telemetry    │  │  • User accounts│  │  • SOC 2 reports│  │
│  │  • Traces       │  │  • App configs  │  │  • Audit exports│  │
│  │  • Metrics      │  │  • Billing      │  │  • Backups      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Fail-Open** | If any component fails, user's app keeps running |
| **Privacy-First** | All PII scrubbed client-side before transmission |
| **Model-Agnostic** | LiteLLM enables instant provider switching |
| **OpenTelemetry Native** | Data format compatible with Datadog/enterprise tools |
| **Zero-Config** | Works with a single import, no configuration required |

### 1.3 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Backend API** | FastAPI (Python 3.11+) | High performance, async, native AI library support |
| **Database** | Supabase (Postgres) | Managed, auto-backups, point-in-time recovery |
| **Log Storage** | OpenObserve | 140x cheaper than Splunk, Rust-based, SOC 2 compliant |
| **AI Router** | LiteLLM | Universal provider translator, automatic failover |
| **Telemetry Format** | OpenTelemetry | Global standard, portable to enterprise tools |
| **Job Queue** | Redis + ARQ | Simple async Python job processing |
| **Frontend Dashboard** | Next.js 14 (App Router) | React, Vercel-native deployment |
| **Visualization** | React Flow | Interactive architecture diagrams |
| **Email Notifications** | Resend | Developer-friendly, reliable delivery |
| **Telegram Bot** | python-telegram-bot | Real-time alert delivery |

---

## 2. SDK Specifications

### 2.1 Python SDK: `codewarden-py`

#### 2.1.1 Installation

```bash
pip install codewarden
```

> ⚠️ **Pre-Launch Verification Required**
> 
> Before publishing, verify package name availability:
> ```bash
> pip index versions codewarden
> ```
> 
> **Fallback names if taken:** `codewarden-io`, `code-warden`, `cw-agent`
> 
> Update all documentation if using a fallback name.

#### 2.1.2 Quick Start

```python
# main.py
from fastapi import FastAPI
from codewarden import CodeWarden

app = FastAPI()

# One-line activation
warden = CodeWarden(app)

# That's it. CodeWarden is now watching.
```

#### 2.1.3 Module Structure

```
codewarden/
├── __init__.py           # Main CodeWarden class
├── middleware/
│   ├── __init__.py
│   ├── fastapi.py        # FastAPI middleware
│   ├── flask.py          # Flask middleware (Phase 2)
│   └── django.py         # Django middleware (Phase 2)
├── scrubber/
│   ├── __init__.py
│   ├── airlock.py        # Main PII scrubbing engine
│   ├── patterns.py       # Regex patterns (from Gitleaks)
│   └── sanitizer.py      # Log sanitization utilities
├── scanner/
│   ├── __init__.py
│   ├── dependencies.py   # pip-audit wrapper
│   ├── secrets.py        # Secret detection in env vars
│   └── code.py           # Bandit integration
├── evidence/
│   ├── __init__.py
│   ├── collector.py      # EvidenceCollector class
│   ├── deploy.py         # Deployment tracking
│   └── access.py         # Access logging
├── notifier/
│   ├── __init__.py
│   ├── email.py          # Resend integration
│   └── telegram.py       # Telegram bot integration
├── handshake/
│   ├── __init__.py
│   ├── setup.py          # Terminal pairing experience
│   ├── telegram.py       # Telegram pairing flow
│   └── email.py          # Email magic link pairing flow
└── config.py             # Configuration management
```

#### 2.1.4 Core Classes

**CodeWarden (Main Entry Point)**

```python
class CodeWarden:
    """
    The main CodeWarden security agent.
    
    Usage:
        from codewarden import CodeWarden
        warden = CodeWarden(app)
    """
    
    def __init__(
        self,
        app: FastAPI,
        api_key: str = None,           # Auto-reads from CODEWARDEN_API_KEY
        scrub_pii: bool = True,        # Enable Airlock
        scan_on_startup: bool = True,  # Run pip-audit on start
        notify_on_crash: bool = True,  # Send alerts for errors
        evidence_logging: bool = True, # Track deployments
        telegram_bot_token: str = None # Optional Telegram integration
    ):
        pass
    
    def report_error(self, error: Exception, context: dict = None) -> None:
        """Manually report an error to CodeWarden."""
        pass
    
    def log_custom_event(self, event_type: str, data: dict) -> None:
        """Log a custom event for the Evidence Locker."""
        pass
    
    def run_security_scan(self) -> ScanResult:
        """Manually trigger a security scan."""
        pass
```

**Airlock (PII Scrubber)**

```python
class Airlock:
    """
    Client-side PII scrubbing engine.
    Runs BEFORE any data leaves the user's server.
    """
    
    # Pattern types to detect
    PATTERNS = {
        'EMAIL': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'CREDIT_CARD': r'\b(?:\d{4}[- ]?){3}\d{4}\b',
        'SSN': r'\b\d{3}-\d{2}-\d{4}\b',
        'API_KEY_OPENAI': r'sk-[a-zA-Z0-9]{48}',
        'API_KEY_STRIPE': r'sk_(live|test)_[a-zA-Z0-9]{24,}',
        'API_KEY_AWS': r'AKIA[0-9A-Z]{16}',
        'API_KEY_GOOGLE': r'AIza[0-9A-Za-z\-_]{35}',
        'PHONE': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'PASSWORD_FIELD': r'(?i)(password|passwd|pwd)\s*[:=]\s*\S+',
        'JWT': r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+',
    }
    
    def scrub(self, text: str) -> str:
        """
        Replace all PII patterns with redaction markers.
        
        Returns:
            Scrubbed text safe for transmission.
        """
        pass
    
    def scrub_dict(self, data: dict) -> dict:
        """Recursively scrub all string values in a dictionary."""
        pass
    
    def is_safe(self, text: str) -> bool:
        """Check if text contains any detectable PII."""
        pass
```

**DependencyScanner (pip-audit Wrapper)**

```python
class DependencyScanner:
    """
    Scans installed packages for known vulnerabilities.
    Uses pip-audit with PyPI/OSV database.
    """
    
    def scan(self) -> list[VulnerabilityReport]:
        """
        Scan current environment for vulnerable packages.
        
        Returns:
            List of VulnerabilityReport objects.
        """
        pass
    
    def get_fix_commands(self, vulnerabilities: list) -> list[str]:
        """
        Generate pip commands to fix vulnerabilities.
        
        Returns:
            List of command strings like "pip install requests>=2.31.0"
        """
        pass

@dataclass
class VulnerabilityReport:
    package: str
    installed_version: str
    vulnerability_id: str  # CVE or GHSA
    severity: str          # LOW, MEDIUM, HIGH, CRITICAL
    fix_version: str | None
    description: str
```

**EvidenceCollector (SOC 2 Compliance)**

```python
class EvidenceCollector:
    """
    Collects and logs compliance-relevant events.
    Generates artifacts for SOC 2 audits.
    """
    
    def log_deployment(
        self,
        version: str,
        commit_hash: str = None,
        deployer: str = "system"
    ) -> None:
        """
        Record a deployment event.
        Auditors need: "Who deployed what, when?"
        """
        pass
    
    def log_security_scan(
        self,
        tool_name: str,
        status: Literal["PASS", "FAIL"],
        issue_count: int,
        details: dict = None
    ) -> None:
        """
        Record a security scan result.
        Auditors need: "Did you check for vulnerabilities?"
        """
        pass
    
    def log_access_event(
        self,
        user_id: str,
        action: str,
        resource: str,
        ip_address: str = None
    ) -> None:
        """
        Record an access/authentication event.
        Auditors need: "Who accessed what?"
        """
        pass
    
    def export_evidence_package(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> bytes:
        """
        Generate a ZIP file with all compliance evidence.
        
        Returns:
            ZIP file bytes containing PDFs and CSVs.
        """
        pass
```

**Handshake Module (Multi-Method Pairing)**

The handshake module provides a flexible pairing experience that supports both Telegram and Email verification, ensuring no user is blocked by their choice of communication tools.

```python
# codewarden/handshake/setup.py
import time
import random
import sys
from enum import Enum
from typing import Optional

class PairingMethod(Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"

def type_writer(text: str, speed: float = 0.03) -> None:
    """Typewriter effect for terminal output."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)
    print("")

def display_header() -> None:
    """Display the CodeWarden activation header."""
    print("\n" + "=" * 50)
    print(" 🛡️   C O D E W A R D E N   (v1.0.0)")
    print("=" * 50)
    
    type_writer("Initializing security protocols...", 0.05)
    time.sleep(0.5)
    type_writer(">> Analyzing environment... Safe.", 0.02)
    type_writer(">> Checking dependencies... Done.", 0.02)

def prompt_pairing_method() -> PairingMethod:
    """Prompt user to select their preferred pairing method."""
    print("\n" + "-" * 50)
    print("🔒  DEVICE NOT PAIRED")
    print("-" * 50)
    print("How would you like to pair this server?\n")
    print("  [1] 📱 Telegram (Recommended - instant alerts)")
    print("  [2] 📧 Email (Works everywhere)")
    print("")
    
    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "1":
            return PairingMethod.TELEGRAM
        elif choice == "2":
            return PairingMethod.EMAIL
        else:
            print("Please enter 1 or 2.")

def generate_pairing_code() -> str:
    """Generate a unique pairing code."""
    return f"CW-{random.randint(1000, 9999)}"

def telegram_pairing_flow(code: str) -> bool:
    """Handle Telegram-based pairing."""
    print("\n" + "-" * 50)
    print("📱  TELEGRAM PAIRING")
    print("-" * 50)
    print("1. Open Telegram")
    print("2. Message @CodeWardenBot")
    print("3. Send this activation code:\n")
    print(f"      🔑  {code}  🔐\n")
    print("Waiting for uplink...", end="", flush=True)
    
    # Poll API for verification (simplified)
    return _poll_for_verification(code, "telegram")

def email_pairing_flow() -> bool:
    """Handle Email-based pairing."""
    print("\n" + "-" * 50)
    print("📧  EMAIL PAIRING")
    print("-" * 50)
    
    email = input("Enter your email address: ").strip()
    
    if not _is_valid_email(email):
        print("❌ Invalid email address. Please try again.")
        return False
    
    print("\nSending verification link...", flush=True)
    
    # Send magic link via API
    success = _send_magic_link(email)
    
    if success:
        print("✅ Check your inbox! Click the link to complete setup.\n")
        print("Waiting for verification...", end="", flush=True)
        return _poll_for_verification(email, "email")
    else:
        print("❌ Failed to send email. Please check your connection.")
        return False

def _poll_for_verification(identifier: str, method: str, timeout: int = 300) -> bool:
    """Poll the API for verification completion."""
    import requests
    
    start_time = time.time()
    dots = 0
    
    while time.time() - start_time < timeout:
        time.sleep(2)
        dots += 1
        print("." * (dots % 4 + 1) + "   \r", end="", flush=True)
        
        try:
            response = requests.get(
                f"https://api.codewarden.io/v1/pairing/status",
                params={"identifier": identifier, "method": method},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("verified"):
                    return True
        except:
            pass
    
    return False

def _is_valid_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def _send_magic_link(email: str) -> bool:
    """Send magic link to email."""
    import requests
    
    try:
        response = requests.post(
            "https://api.codewarden.io/v1/pairing/email",
            json={"email": email},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

def display_success(user_name: str, method: PairingMethod) -> None:
    """Display success message after pairing."""
    print("\n")
    if method == PairingMethod.TELEGRAM:
        print("✅ UPLINK ESTABLISHED.")
    else:
        print("✅ EMAIL VERIFIED.")
    
    type_writer(f"User identified: {user_name}", 0.05)
    type_writer("Security Level: OFFICER (Active)", 0.05)
    print("\nCodeWarden is watching your back. Happy building.\n")
    
    if method == PairingMethod.EMAIL:
        print("💡 Tip: Add Telegram later for instant mobile alerts.")
        print("   Dashboard → Settings → Notifications\n")

def start_setup() -> Optional[str]:
    """
    Main entry point for the pairing flow.
    Returns the API key on success, None on failure.
    """
    display_header()
    
    method = prompt_pairing_method()
    
    if method == PairingMethod.TELEGRAM:
        code = generate_pairing_code()
        success = telegram_pairing_flow(code)
    else:
        success = email_pairing_flow()
    
    if success:
        display_success("User", method)
        # Return API key from server response
        return "cw_live_xxxxx"
    else:
        print("\n❌ Pairing timed out. Please try again.")
        return None

if __name__ == "__main__":
    start_setup()
```

#### 2.1.5 Middleware Implementation

```python
# codewarden/middleware/fastapi.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import traceback

class CodeWardenMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that intercepts all requests.
    
    Responsibilities:
    1. Log request/response metadata
    2. Catch and report unhandled exceptions
    3. Track response times for latency monitoring
    4. Scrub any PII before logging
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Generate trace ID for request correlation
        trace_id = self._generate_trace_id()
        
        try:
            response = await call_next(request)
            
            # Log successful request
            self._log_request(
                trace_id=trace_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=(time.time() - start_time) * 1000
            )
            
            return response
            
        except Exception as e:
            # Scrub the stack trace
            safe_trace = self.airlock.scrub(traceback.format_exc())
            
            # Report to CodeWarden API
            await self._report_crash(
                trace_id=trace_id,
                error=str(e),
                error_type=type(e).__name__,
                trace=safe_trace,
                request_path=request.url.path,
                request_method=request.method
            )
            
            # Re-raise to let FastAPI handle the error response
            raise
```

### 2.2 JavaScript SDK: `codewarden-js`

#### 2.2.1 Installation

```bash
npm install codewarden-js
# or
yarn add codewarden-js
```

#### 2.2.2 Next.js Integration

```typescript
// instrumentation.ts (Next.js App Router)
import { CodeWarden } from 'codewarden-js';

export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    const warden = new CodeWarden({
      apiKey: process.env.CODEWARDEN_API_KEY,
    });
    
    await warden.initialize();
  }
}
```

#### 2.2.3 Module Structure

```
codewarden-js/
├── src/
│   ├── index.ts              # Main exports
│   ├── CodeWarden.ts         # Main class
│   ├── middleware/
│   │   ├── nextjs.ts         # Next.js instrumentation
│   │   └── express.ts        # Express middleware (Phase 2)
│   ├── guards/
│   │   ├── console.ts        # Console.log override
│   │   ├── network.ts        # Fetch/XHR interceptor
│   │   └── error-boundary.tsx # React error boundary
│   ├── scrubber/
│   │   ├── airlock.ts        # PII scrubbing
│   │   └── patterns.ts       # Regex patterns
│   └── types/
│       └── index.ts          # TypeScript definitions
├── package.json
└── tsconfig.json
```

#### 2.2.4 Core Features

**Console Guard**

```typescript
// Prevents accidental secret leakage in browser console
class ConsoleGuard {
  private originalLog: typeof console.log;
  private airlock: Airlock;
  
  install(): void {
    if (process.env.NODE_ENV === 'production') {
      this.originalLog = console.log;
      
      console.log = (...args) => {
        // Scrub each argument
        const safeArgs = args.map(arg => 
          typeof arg === 'string' ? this.airlock.scrub(arg) : arg
        );
        
        // Check for potential secrets
        if (this.containsSecrets(args)) {
          this.reportPotentialLeak(args);
          return; // Don't log at all
        }
        
        this.originalLog(...safeArgs);
      };
    }
  }
}
```

**Network Spy**

```typescript
// Tracks failed API requests
class NetworkSpy {
  install(): void {
    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      try {
        const response = await originalFetch(...args);
        
        if (!response.ok) {
          this.reportFailedRequest({
            url: args[0],
            status: response.status,
            statusText: response.statusText
          });
        }
        
        return response;
      } catch (error) {
        this.reportNetworkError({
          url: args[0],
          error: error.message
        });
        throw error;
      }
    };
  }
}
```

**React Error Boundary**

```tsx
// Catch and report React rendering errors
import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

export class CodeWardenErrorBoundary extends Component<Props> {
  state = { hasError: false };
  
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    CodeWarden.reportError({
      error: error.message,
      componentStack: errorInfo.componentStack,
      type: 'react_render_error'
    });
  }
  
  render() {
    if (this.state.hasError) {
      return this.props.fallback || <h1>Something went wrong.</h1>;
    }
    return this.props.children;
  }
}
```

---

## 3. API Specifications

### 3.1 Base URL

```
Production: https://api.codewarden.io/v1
Staging:    https://staging-api.codewarden.io/v1
```

### 3.2 Authentication

All requests require Bearer token authentication:

```http
Authorization: Bearer <CODEWARDEN_API_KEY>
```

API keys are formatted as: `cw_live_xxxxxxxxxxxxxxxxxxxx` or `cw_test_xxxxxxxxxxxxxxxxxxxx`

### 3.3 Endpoints

#### 3.3.1 Telemetry Ingestion

**POST /v1/telemetry**

Receives error logs, traces, and metrics from SDKs.

```http
POST /v1/telemetry
Content-Type: application/json
Authorization: Bearer cw_live_xxxxxxxxxxxx

{
  "source": "backend-fastapi",
  "type": "crash",
  "severity": "critical",
  "app_id": "app_abc123",
  "environment": "production",
  "payload": {
    "error_type": "ZeroDivisionError",
    "error_message": "division by zero",
    "file": "services/pricing.py",
    "line": 45,
    "function": "calculate_discount",
    "trace_scrubbed": "Traceback (most recent call last):\n  File \"services/pricing.py\", line 45...",
    "context": {
      "request_path": "/api/checkout",
      "request_method": "POST",
      "user_id": "[USER_REDACTED]"
    }
  },
  "timestamp": "2026-01-04T10:00:00Z",
  "trace_id": "abc123def456"
}
```

**Response (201 Created)**

```json
{
  "id": "evt_xxxxxxxxxx",
  "status": "received",
  "analysis_status": "queued"
}
```

#### 3.3.2 Evidence Logging

**POST /v1/evidence**

Logs compliance-relevant events for SOC 2.

```http
POST /v1/evidence
Content-Type: application/json
Authorization: Bearer cw_live_xxxxxxxxxxxx

{
  "type": "AUDIT_DEPLOY",
  "app_id": "app_abc123",
  "data": {
    "version": "v1.0.4",
    "commit_hash": "abc123def",
    "deployer": "github-actions",
    "runtime": "python3.11"
  },
  "timestamp": "2026-01-04T10:00:00Z"
}
```

**Event Types:**

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `AUDIT_DEPLOY` | Deployment record | version, commit_hash |
| `AUDIT_SCAN` | Security scan result | tool, status, issue_count |
| `AUDIT_ACCESS` | Authentication event | user_id, action, resource |
| `AUDIT_CONFIG` | Configuration change | setting, old_value, new_value |

#### 3.3.3 Health Check

**GET /v1/health**

SDK health check and configuration sync.

```http
GET /v1/health
Authorization: Bearer cw_live_xxxxxxxxxxxx
```

**Response (200 OK)**

```json
{
  "status": "healthy",
  "app": {
    "id": "app_abc123",
    "name": "my-saas-app",
    "plan": "pro"
  },
  "config": {
    "scrub_pii": true,
    "scan_on_startup": true,
    "notification_channels": ["email", "telegram"]
  },
  "rate_limit": {
    "remaining": 4850,
    "limit": 5000,
    "reset_at": "2026-01-04T11:00:00Z"
  }
}
```

#### 3.3.4 Analysis Retrieval

**GET /v1/events/{event_id}/analysis**

Retrieve AI analysis for a specific event.

```http
GET /v1/events/evt_xxxxxxxxxx/analysis
Authorization: Bearer cw_live_xxxxxxxxxxxx
```

**Response (200 OK)**

```json
{
  "event_id": "evt_xxxxxxxxxx",
  "analysis": {
    "summary": "Your checkout endpoint crashed because the discount calculation tried to divide by zero when the cart was empty.",
    "severity": "critical",
    "root_cause": "Missing empty cart check in calculate_discount()",
    "fix_suggestion": "Add a guard clause: `if not cart_items: return 0`",
    "fix_code": "def calculate_discount(cart_items):\n    if not cart_items:\n        return 0\n    # ... rest of function",
    "related_docs": [
      "https://docs.python.org/3/tutorial/errors.html"
    ]
  },
  "model_used": "gemini-1.5-flash",
  "analyzed_at": "2026-01-04T10:00:05Z"
}
```

#### 3.3.5 SOC 2 Evidence Export

**POST /v1/evidence/export**

Generate SOC 2 evidence package.

```http
POST /v1/evidence/export
Content-Type: application/json
Authorization: Bearer cw_live_xxxxxxxxxxxx

{
  "app_id": "app_abc123",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "include": ["deployments", "scans", "access_logs", "uptime"]
}
```

**Response (202 Accepted)**

```json
{
  "export_id": "exp_xxxxxxxxxx",
  "status": "processing",
  "estimated_completion": "2026-01-04T10:05:00Z",
  "download_url": null
}
```

**GET /v1/evidence/export/{export_id}**

Check export status and get download URL.

```json
{
  "export_id": "exp_xxxxxxxxxx",
  "status": "complete",
  "download_url": "https://cdn.codewarden.io/exports/exp_xxxxxxxxxx.zip",
  "expires_at": "2026-01-05T10:00:00Z",
  "contents": {
    "deployments": 156,
    "security_scans": 365,
    "access_events": 2340,
    "uptime_reports": 12
  }
}
```

### 3.4 Rate Limits

| Plan | Requests/Hour | Events/Month |
|------|---------------|--------------|
| Hobbyist | 100 | 1,000 |
| Builder | 1,000 | 50,000 |
| Pro | 5,000 | 500,000 |
| Team | 20,000 | 2,000,000 |
| Enterprise | Unlimited | Unlimited |

Rate limit headers included in all responses:

```http
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4850
X-RateLimit-Reset: 1704362400
```

### 3.5 Error Responses

**Standard Error Format**

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "You have exceeded your hourly rate limit.",
    "details": {
      "limit": 5000,
      "reset_at": "2026-01-04T11:00:00Z"
    }
  }
}
```

**Error Codes**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_api_key` | 401 | API key is invalid or expired |
| `rate_limit_exceeded` | 429 | Too many requests |
| `invalid_payload` | 400 | Request body validation failed |
| `app_not_found` | 404 | App ID doesn't exist |
| `plan_limit_exceeded` | 403 | Event quota exhausted |
| `internal_error` | 500 | Server-side error |

---

## 4. AI Analysis Engine

### 4.1 LiteLLM Router Configuration

```python
# codewarden/brain/router.py
from litellm import completion, acompletion
import os

class AIRouter:
    """
    Model-agnostic AI router using LiteLLM.
    Enables instant switching between providers.
    """
    
    MODEL_CONFIG = {
        # Fast mode: Cheap, quick responses
        "fast": {
            "model": "gemini/gemini-1.5-flash",
            "max_tokens": 1000,
            "temperature": 0.3
        },
        # Smart mode: Best for complex debugging
        "smart": {
            "model": "anthropic/claude-3-5-sonnet-20241022",
            "max_tokens": 2000,
            "temperature": 0.2
        },
        # Fallback: When primary providers fail
        "fallback": {
            "model": "openai/gpt-4o-mini",
            "max_tokens": 1000,
            "temperature": 0.3
        }
    }
    
    SYSTEM_PROMPT = """You are a Senior DevOps Engineer helping a non-technical founder.

Your task is to explain errors in plain English that anyone can understand.

Rules:
1. No jargon. Explain like they've never coded before.
2. Be direct. Lead with what broke and how to fix it.
3. Provide the exact code fix when possible.
4. Keep explanations under 3 sentences.

Output JSON format:
{
  "summary": "One sentence explaining what went wrong",
  "root_cause": "Technical cause in simple terms",
  "fix_suggestion": "What they should do",
  "fix_code": "The corrected code snippet (if applicable)",
  "severity": "critical|high|medium|low"
}"""
    
    async def analyze(
        self,
        error_data: dict,
        mode: str = "fast"
    ) -> dict:
        """Analyze an error and return plain-English explanation."""
        
        config = self.MODEL_CONFIG.get(mode, self.MODEL_CONFIG["fast"])
        
        user_message = f"""Error: {error_data.get('error_type')}: {error_data.get('error_message')}

File: {error_data.get('file')}, Line: {error_data.get('line')}

Stack Trace:
{error_data.get('trace_scrubbed', 'No trace available')}

Context:
{error_data.get('context', {})}"""
        
        try:
            response = await acompletion(
                model=config["model"],
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                fallbacks=[self.MODEL_CONFIG["fallback"]["model"]]
            )
            
            return self._parse_response(response.choices[0].message.content)
            
        except Exception as e:
            return {
                "summary": "Analysis temporarily unavailable",
                "root_cause": str(e),
                "fix_suggestion": "Please check the dashboard for more details",
                "severity": "unknown"
            }
```

### 4.2 Consensus Check (Multi-Model Verification)

For critical security alerts, we run the same prompt through multiple models:

```python
import asyncio
from collections import Counter

async def consensus_check(self, error_data: dict) -> dict:
    """
    Run analysis through 3 models and compare results.
    Used for high-stakes security decisions.
    """
    
    prompt = self._build_security_prompt(error_data)
    
    # Fire 3 models simultaneously
    tasks = [
        acompletion(
            model="gemini/gemini-1.5-flash",
            messages=[{"role": "user", "content": prompt}]
        ),
        acompletion(
            model="anthropic/claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": prompt}]
        ),
        acompletion(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Parse verdicts (SAFE / ATTACK / UNCERTAIN)
    verdicts = []
    for r in results:
        if not isinstance(r, Exception):
            verdict = self._extract_verdict(r.choices[0].message.content)
            verdicts.append(verdict)
    
    # Majority vote
    vote_counts = Counter(verdicts)
    winner, count = vote_counts.most_common(1)[0]
    
    return {
        "verdict": winner,
        "confidence": count / len(verdicts),
        "models_agreed": count,
        "models_total": len(verdicts),
        "details": verdicts
    }
```

### 4.3 Prompt Templates

**Error Analysis Prompt**

```
Role: Senior DevOps Engineer
Audience: Non-technical founder who just wants their app to work
Task: Explain this error in 1 sentence of plain English. Then provide the fixed code.

Error Details:
{error_data}

Rules:
- No acronyms without explanation
- Lead with what the user should DO
- Code fixes should be copy-paste ready
```

**Security Assessment Prompt**

```
Role: Security Analyst
Task: Determine if this log pattern indicates a security threat.

Log Data:
{log_data}

Respond with exactly one of:
- SAFE: Normal application behavior
- ATTACK: Potential security threat (SQL injection, XSS, etc.)
- UNCERTAIN: Cannot determine, needs human review

Then explain your reasoning in 2 sentences.
```

**Daily Summary Prompt**

```
Role: Friendly DevOps Assistant
Task: Write a brief daily summary email for a busy founder.

Stats from last 24 hours:
- Errors: {error_count}
- Warnings: {warning_count}
- Requests: {request_count}
- Uptime: {uptime_percentage}%
- Security scans: {scan_status}

Tone: Casual, reassuring, emoji-friendly
Length: 4-6 sentences max
```

---

## 5. Security Stack

### 5.1 Dependency Vulnerability Scanning

**Tool:** `pip-audit` (Python), `npm audit` (Node.js)

```python
# codewarden/scanner/dependencies.py
import subprocess
import json
from dataclasses import dataclass

@dataclass
class Vulnerability:
    package: str
    installed_version: str
    vulnerability_id: str
    severity: str
    fix_version: str | None
    description: str

class DependencyScanner:
    """Wraps pip-audit for vulnerability detection."""
    
    def scan_python_environment(self) -> list[Vulnerability]:
        """Run pip-audit on current environment."""
        
        result = subprocess.run(
            ["pip-audit", "--format", "json", "--progress-spinner", "off"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0 and not result.stdout:
            return []
        
        data = json.loads(result.stdout)
        vulnerabilities = []
        
        for item in data.get("dependencies", []):
            for vuln in item.get("vulns", []):
                vulnerabilities.append(Vulnerability(
                    package=item["name"],
                    installed_version=item["version"],
                    vulnerability_id=vuln["id"],
                    severity=self._map_severity(vuln.get("fix_versions", [])),
                    fix_version=vuln["fix_versions"][0] if vuln.get("fix_versions") else None,
                    description=vuln.get("description", "")
                ))
        
        return vulnerabilities
    
    def generate_fix_commands(self, vulns: list[Vulnerability]) -> list[str]:
        """Generate pip install commands to fix vulnerabilities."""
        commands = []
        for v in vulns:
            if v.fix_version:
                commands.append(f"pip install {v.package}>={v.fix_version}")
        return commands
```

### 5.2 Static Code Analysis

**Tool:** `bandit` (Python)

```python
# codewarden/scanner/code.py
from bandit.core import manager as bandit_manager
from bandit.core import config as bandit_config

class CodeScanner:
    """Static analysis for security issues in Python code."""
    
    # Enabled checks (skip noisy/low-value rules)
    ENABLED_TESTS = [
        "B101",  # assert_used
        "B102",  # exec_used
        "B103",  # set_bad_file_permissions
        "B104",  # hardcoded_bind_all_interfaces
        "B105",  # hardcoded_password_string
        "B106",  # hardcoded_password_funcarg
        "B107",  # hardcoded_password_default
        "B108",  # hardcoded_tmp_directory
        "B110",  # try_except_pass
        "B112",  # try_except_continue
        "B201",  # flask_debug_true
        "B301",  # pickle
        "B302",  # marshal
        "B303",  # md5
        "B304",  # des
        "B305",  # cipher
        "B306",  # mktemp_q
        "B307",  # eval
        "B308",  # mark_safe
        "B310",  # urllib_urlopen
        "B311",  # random
        "B312",  # telnetlib
        "B313",  # xml_bad_cElementTree
        "B320",  # xml_bad_sax
        "B323",  # unverified_context
        "B324",  # hashlib_insecure
        "B501",  # request_with_no_cert_validation
        "B502",  # ssl_with_bad_version
        "B503",  # ssl_with_bad_defaults
        "B504",  # ssl_with_no_version
        "B505",  # weak_cryptographic_key
        "B506",  # yaml_load
        "B507",  # ssh_no_host_key_verification
        "B601",  # paramiko_calls
        "B602",  # subprocess_popen_with_shell_equals_true
        "B604",  # any_other_function_with_shell_equals_true
        "B605",  # start_process_with_a_shell
        "B606",  # start_process_with_no_shell
        "B607",  # start_process_with_partial_path
        "B608",  # hardcoded_sql_expressions
        "B609",  # wildcard_injection
        "B610",  # django_extra_used
        "B611",  # django_rawsql_used
        "B701",  # jinja2_autoescape_false
        "B702",  # use_of_mako_templates
        "B703",  # django_mark_safe
    ]
    
    def scan_directory(self, path: str) -> list[dict]:
        """Scan a directory for security issues."""
        
        conf = bandit_config.BanditConfig()
        mgr = bandit_manager.BanditManager(conf, "file")
        
        mgr.discover_files([path])
        mgr.run_tests()
        
        issues = []
        for item in mgr.get_issue_list():
            issues.append({
                "severity": item.severity,
                "confidence": item.confidence,
                "file": item.fname,
                "line": item.lineno,
                "test_id": item.test_id,
                "issue": item.text,
                "code": item.get_code()
            })
        
        return issues
```

### 5.3 Secret Detection

**Based on:** Gitleaks regex patterns

```python
# codewarden/scanner/secrets.py
import re
import os

class SecretScanner:
    """Detects hardcoded secrets in code and environment variables."""
    
    # Patterns from Gitleaks project (open source)
    PATTERNS = {
        "aws_access_key": {
            "pattern": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
            "severity": "critical"
        },
        "aws_secret_key": {
            "pattern": r"(?i)aws(.{0,20})?['\"][0-9a-zA-Z\/+]{40}['\"]",
            "severity": "critical"
        },
        "github_token": {
            "pattern": r"ghp_[0-9a-zA-Z]{36}",
            "severity": "high"
        },
        "github_oauth": {
            "pattern": r"gho_[0-9a-zA-Z]{36}",
            "severity": "high"
        },
        "openai_api_key": {
            "pattern": r"sk-[a-zA-Z0-9]{48}",
            "severity": "critical"
        },
        "stripe_live_key": {
            "pattern": r"sk_live_[0-9a-zA-Z]{24,}",
            "severity": "critical"
        },
        "stripe_test_key": {
            "pattern": r"sk_test_[0-9a-zA-Z]{24,}",
            "severity": "medium"
        },
        "google_api_key": {
            "pattern": r"AIza[0-9A-Za-z\-_]{35}",
            "severity": "high"
        },
        "slack_token": {
            "pattern": r"xox[baprs]-[0-9]{10,13}-[0-9a-zA-Z]{24}",
            "severity": "high"
        },
        "jwt_token": {
            "pattern": r"eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+",
            "severity": "medium"
        },
        "private_key": {
            "pattern": r"-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
            "severity": "critical"
        },
        "generic_secret": {
            "pattern": r"(?i)(api[_-]?key|apikey|secret|password|passwd|pwd|token)['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{16,}['\"]",
            "severity": "medium"
        }
    }
    
    def scan_text(self, text: str) -> list[dict]:
        """Scan text for secrets."""
        findings = []
        
        for name, config in self.PATTERNS.items():
            matches = re.finditer(config["pattern"], text)
            for match in matches:
                findings.append({
                    "type": name,
                    "severity": config["severity"],
                    "match": self._redact(match.group()),
                    "position": match.start()
                })
        
        return findings
    
    def scan_environment(self) -> list[dict]:
        """Scan environment variables for exposed secrets."""
        findings = []
        
        for key, value in os.environ.items():
            for secret in self.scan_text(value):
                findings.append({
                    **secret,
                    "env_var": key,
                    "recommendation": f"Move {key} to a secrets manager"
                })
        
        return findings
    
    def _redact(self, secret: str) -> str:
        """Redact a secret for safe display."""
        if len(secret) <= 8:
            return "*" * len(secret)
        return secret[:4] + "*" * (len(secret) - 8) + secret[-4:]
```

---

## 6. Data Storage

### 6.1 OpenObserve Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  openobserve:
    image: openobserve/openobserve:latest
    environment:
      ZO_ROOT_USER_EMAIL: admin@codewarden.io
      ZO_ROOT_USER_PASSWORD: ${OPENOBSERVE_PASSWORD}
      ZO_DATA_DIR: /data
    volumes:
      - openobserve-data:/data
    ports:
      - "5080:5080"
    restart: unless-stopped

volumes:
  openobserve-data:
```

### 6.2 Database Schema (Supabase/Postgres)

```sql
-- Users and Organizations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    plan TEXT DEFAULT 'hobbyist',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    org_id UUID REFERENCES organizations(id),
    telegram_chat_id TEXT,
    notification_preferences JSONB DEFAULT '{"email": true, "telegram": false}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Applications
CREATE TABLE apps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    name TEXT NOT NULL,
    api_key TEXT UNIQUE NOT NULL,
    environment TEXT DEFAULT 'production',
    last_seen_at TIMESTAMPTZ,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_apps_api_key ON apps(api_key);

-- Events (stored in OpenObserve, this is for metadata)
CREATE TABLE event_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_id UUID REFERENCES apps(id),
    event_type TEXT NOT NULL,
    severity TEXT,
    openobserve_id TEXT,
    analysis_status TEXT DEFAULT 'pending',
    analysis_result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_app ON event_metadata(app_id);
CREATE INDEX idx_events_created ON event_metadata(created_at);

-- Evidence Locker
CREATE TABLE evidence_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_id UUID REFERENCES apps(id),
    event_type TEXT NOT NULL,  -- AUDIT_DEPLOY, AUDIT_SCAN, etc.
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_evidence_app_type ON evidence_events(app_id, event_type);
CREATE INDEX idx_evidence_created ON evidence_events(created_at);

-- API Keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    key_hash TEXT UNIQUE NOT NULL,
    key_prefix TEXT NOT NULL,  -- First 8 chars for display
    name TEXT,
    permissions JSONB DEFAULT '["read", "write"]',
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 6.3 Data Retention Policy

| Plan | Event Retention | Evidence Retention |
|------|-----------------|-------------------|
| Hobbyist | 7 days | 30 days |
| Builder | 30 days | 90 days |
| Pro | 90 days | 1 year |
| Team | 1 year | 3 years |
| Enterprise | Custom | Custom |

---

## 7. Notification System

### 7.1 Email Templates (Resend)

**Crash Alert Template**

```html
<!-- templates/crash_alert.html -->
<!DOCTYPE html>
<html>
<head>
  <style>
    .alert-header { background: #EF4444; color: white; padding: 20px; }
    .code-block { background: #1F2937; color: #10B981; padding: 15px; font-family: monospace; }
    .fix-section { background: #ECFDF5; border-left: 4px solid #10B981; padding: 15px; }
  </style>
</head>
<body>
  <div class="alert-header">
    <h1>🚨 Critical Error in {{ app_name }}</h1>
  </div>
  
  <div style="padding: 20px;">
    <h2>What Happened</h2>
    <p>{{ analysis.summary }}</p>
    
    <h3>📍 Location</h3>
    <p><code>{{ file }}:{{ line }}</code> in <code>{{ function }}()</code></p>
    
    <h3>🔍 Root Cause</h3>
    <p>{{ analysis.root_cause }}</p>
    
    <div class="fix-section">
      <h3>💡 How to Fix</h3>
      <p>{{ analysis.fix_suggestion }}</p>
      
      {% if analysis.fix_code %}
      <div class="code-block">
        <pre>{{ analysis.fix_code }}</pre>
      </div>
      {% endif %}
    </div>
    
    <p style="margin-top: 30px;">
      <a href="{{ dashboard_url }}" style="background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
        View in Dashboard →
      </a>
    </p>
  </div>
</body>
</html>
```

**Daily Brief Template**

```html
<!-- templates/daily_brief.html -->
<!DOCTYPE html>
<html>
<head>
  <style>
    .status-green { color: #10B981; }
    .status-yellow { color: #F59E0B; }
    .status-red { color: #EF4444; }
    .stat-box { display: inline-block; padding: 15px; margin: 5px; background: #F3F4F6; border-radius: 8px; }
  </style>
</head>
<body>
  <div style="padding: 20px;">
    <h1>☀️ Good morning! Your CodeWarden Daily Brief</h1>
    
    <h2 class="status-{{ overall_status }}">
      {% if overall_status == 'green' %}✅ All Systems Healthy{% endif %}
      {% if overall_status == 'yellow' %}⚠️ Minor Issues Detected{% endif %}
      {% if overall_status == 'red' %}🚨 Action Required{% endif %}
    </h2>
    
    <div style="margin: 20px 0;">
      <div class="stat-box">
        <strong>Errors</strong><br>
        <span style="font-size: 24px;">{{ error_count }}</span>
      </div>
      <div class="stat-box">
        <strong>Warnings</strong><br>
        <span style="font-size: 24px;">{{ warning_count }}</span>
      </div>
      <div class="stat-box">
        <strong>Requests</strong><br>
        <span style="font-size: 24px;">{{ request_count }}</span>
      </div>
      <div class="stat-box">
        <strong>Uptime</strong><br>
        <span style="font-size: 24px;">{{ uptime }}%</span>
      </div>
    </div>
    
    <h3>🔒 Security Status</h3>
    <p>{{ security_summary }}</p>
    
    {% if action_items %}
    <h3>📋 Action Items</h3>
    <ul>
      {% for item in action_items %}
      <li>{{ item }}</li>
      {% endfor %}
    </ul>
    {% endif %}
    
    <p style="margin-top: 30px; color: #6B7280;">
      Have a productive day! 🚀<br>
      — Your CodeWarden
    </p>
  </div>
</body>
</html>
```

### 7.2 Telegram Bot

```python
# codewarden/notifier/telegram.py
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

class CodeWardenBot:
    """Telegram bot for real-time alerts and commands."""
    
    def __init__(self, token: str):
        self.bot = Bot(token)
        self.app = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.handle_start))
        self.app.add_handler(CommandHandler("status", self.handle_status))
        self.app.add_handler(CommandHandler("scan", self.handle_scan))
        self.app.add_handler(MessageHandler(
            filters.Regex(r"^CW-\d{4}$"),
            self.handle_pairing_code
        ))
    
    async def handle_start(self, update: Update, context):
        await update.message.reply_text(
            "🛡️ Welcome to CodeWarden!\n\n"
            "To connect your app, run `codewarden` in your terminal "
            "and send me the pairing code (e.g., CW-1234)."
        )
    
    async def handle_pairing_code(self, update: Update, context):
        code = update.message.text
        chat_id = update.effective_chat.id
        
        # Verify code and link account
        success = await self._link_account(code, chat_id)
        
        if success:
            await update.message.reply_text(
                "✅ UPLINK ESTABLISHED!\n\n"
                "Your app is now connected. I'll alert you instantly "
                "when something needs attention.\n\n"
                "Commands:\n"
                "/status - Check app health\n"
                "/scan - Run security scan"
            )
        else:
            await update.message.reply_text(
                "❌ Invalid or expired code. Please try again."
            )
    
    async def send_crash_alert(self, chat_id: str, event: dict):
        """Send a crash alert to the user."""
        message = (
            f"🚨 *CRITICAL ERROR*\n\n"
            f"*App:* {event['app_name']}\n"
            f"*Error:* `{event['error_type']}`\n\n"
            f"{event['analysis']['summary']}\n\n"
            f"📍 `{event['file']}:{event['line']}`\n\n"
            f"💡 *Fix:* {event['analysis']['fix_suggestion']}\n\n"
            f"[View in Dashboard]({event['dashboard_url']})"
        )
        
        await self.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown"
        )
```

---

## 8. Dashboard Specifications

### 8.1 Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | Next.js 14 (App Router) |
| Styling | Tailwind CSS |
| State Management | TanStack Query |
| Charts | Recharts |
| Architecture Diagrams | React Flow |
| Authentication | Magic Link (Passwordless) |
| Hosting | Vercel |

### 8.2 Page Structure

```
/
├── (auth)/
│   ├── login/           # Magic link login
│   └── verify/          # Email verification callback
├── (dashboard)/
│   ├── layout.tsx       # Dashboard shell with sidebar
│   ├── page.tsx         # Overview / Home
│   ├── apps/
│   │   ├── page.tsx     # List all apps
│   │   └── [id]/
│   │       ├── page.tsx         # App overview
│   │       ├── errors/          # Error log
│   │       ├── map/             # Visual architecture
│   │       └── settings/        # App configuration
│   ├── security/
│   │   ├── page.tsx     # Security overview
│   │   ├── scans/       # Vulnerability scan history
│   │   └── secrets/     # Secret detection alerts
│   ├── compliance/
│   │   ├── page.tsx     # SOC 2 dashboard
│   │   ├── evidence/    # Evidence Locker
│   │   └── export/      # Generate reports
│   └── settings/
│       ├── page.tsx     # Account settings
│       ├── team/        # Team management
│       ├── billing/     # Subscription
│       └── api-keys/    # API key management
└── api/                 # Next.js API routes
```

### 8.3 Responsive Design & Mobile Experience

**Critical Insight:** Solopreneurs check their app health from their phone while at dinner. Complex React Flow maps are unusable on mobile. The dashboard MUST be mobile-first.

#### 8.3.1 Breakpoint Strategy

| Breakpoint | Width | Layout |
|------------|-------|--------|
| **Mobile** | < 768px | Single column, bottom nav, simplified views |
| **Tablet** | 768px - 1024px | Collapsed sidebar, 2-column grids |
| **Desktop** | > 1024px | Full sidebar, Visual Map, multi-column |

#### 8.3.2 Mobile-Specific Components

**Mobile Status Cards (replaces Visual Map on mobile):**

```tsx
// components/mobile/StatusCardList.tsx
interface AppStatus {
  id: string;
  name: string;
  status: 'healthy' | 'warning' | 'critical';
  lastError?: string;
  errorCount: number;
}

export function MobileStatusList({ apps }: { apps: AppStatus[] }) {
  return (
    <div className="space-y-3 p-4">
      {apps.map(app => (
        <div 
          key={app.id}
          className={cn(
            "p-4 rounded-xl border-l-4 bg-white shadow-sm",
            app.status === 'healthy' && "border-l-green-500",
            app.status === 'warning' && "border-l-amber-500",
            app.status === 'critical' && "border-l-red-500"
          )}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <StatusDot status={app.status} />
              <span className="font-medium">{app.name}</span>
            </div>
            <ChevronRight className="text-gray-400" />
          </div>
          
          {app.status !== 'healthy' && (
            <p className="mt-2 text-sm text-gray-600 truncate">
              {app.lastError}
            </p>
          )}
          
          <div className="mt-2 flex gap-4 text-xs text-gray-500">
            <span>{app.errorCount} errors today</span>
          </div>
        </div>
      ))}
    </div>
  );
}
```

**Mobile Bottom Navigation:**

```tsx
// components/mobile/BottomNav.tsx
export function MobileBottomNav() {
  const pathname = usePathname();
  
  const navItems = [
    { href: '/', icon: Home, label: 'Home' },
    { href: '/apps', icon: Grid, label: 'Apps' },
    { href: '/security', icon: Shield, label: 'Security' },
    { href: '/settings', icon: Settings, label: 'Settings' },
  ];
  
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t md:hidden">
      <div className="flex justify-around py-2">
        {navItems.map(item => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-col items-center p-2 rounded-lg",
              pathname === item.href 
                ? "text-blue-600" 
                : "text-gray-500"
            )}
          >
            <item.icon size={24} />
            <span className="text-xs mt-1">{item.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
```

**Mobile Alert Swipe Actions:**

```tsx
// components/mobile/SwipeableErrorCard.tsx
import { useSwipeable } from 'react-swipeable';

export function SwipeableErrorCard({ error, onDismiss, onViewDetails }) {
  const handlers = useSwipeable({
    onSwipedLeft: () => onDismiss(error.id),
    onSwipedRight: () => onViewDetails(error.id),
    trackMouse: true
  });
  
  return (
    <div {...handlers} className="relative overflow-hidden">
      {/* Swipe hint backgrounds */}
      <div className="absolute inset-y-0 left-0 w-20 bg-blue-500 flex items-center justify-center">
        <Eye className="text-white" />
      </div>
      <div className="absolute inset-y-0 right-0 w-20 bg-gray-400 flex items-center justify-center">
        <X className="text-white" />
      </div>
      
      {/* Card content */}
      <div className="relative bg-white p-4 transform transition-transform">
        <ErrorCardContent error={error} />
      </div>
    </div>
  );
}
```

#### 8.3.3 View Mode Switching

The dashboard automatically switches views based on screen size, but users can also manually toggle:

```tsx
// components/ViewModeToggle.tsx
type ViewMode = 'cards' | 'map' | 'table';

export function ViewModeToggle({ 
  currentMode, 
  onChange,
  availableModes 
}: {
  currentMode: ViewMode;
  onChange: (mode: ViewMode) => void;
  availableModes: ViewMode[];
}) {
  // On mobile, 'map' mode is disabled
  const isMobile = useMediaQuery('(max-width: 768px)');
  const modes = isMobile 
    ? availableModes.filter(m => m !== 'map')
    : availableModes;
  
  return (
    <div className="flex rounded-lg bg-gray-100 p-1">
      {modes.map(mode => (
        <button
          key={mode}
          onClick={() => onChange(mode)}
          className={cn(
            "px-3 py-1.5 rounded-md text-sm transition",
            currentMode === mode && "bg-white shadow"
          )}
        >
          {mode === 'cards' && <LayoutGrid size={16} />}
          {mode === 'map' && <Map size={16} />}
          {mode === 'table' && <List size={16} />}
        </button>
      ))}
    </div>
  );
}
```

#### 8.3.4 Mobile-First Feature Parity

| Feature | Desktop | Mobile |
|---------|---------|--------|
| **App Overview** | Visual Map with React Flow | Status Card List |
| **Error List** | Full table with columns | Swipeable cards |
| **Error Details** | Side panel overlay | Full-screen modal |
| **Security Scans** | Table with expand | Accordion list |
| **Evidence Export** | Inline download | Share sheet integration |
| **Settings** | Tab-based layout | Stacked sections |
| **Navigation** | Left sidebar | Bottom tab bar |

#### 8.3.5 Push Notifications (Mobile)

For mobile users, supplement email/Telegram with native push:

```typescript
// lib/notifications/push.ts
export async function registerPushNotifications() {
  if (!('Notification' in window)) return;
  
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') return;
  
  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: process.env.NEXT_PUBLIC_VAPID_KEY
  });
  
  // Send subscription to backend
  await fetch('/api/push/subscribe', {
    method: 'POST',
    body: JSON.stringify(subscription)
  });
}
```

**Mobile Notification Priority:**

| Severity | Push | Sound | Vibration |
|----------|------|-------|-----------|
| Critical | ✅ Immediate | 🔊 Alert tone | 📳 Long pulse |
| Warning | ✅ Immediate | 🔇 Silent | 📳 Short pulse |
| Info | ❌ Batched (hourly) | 🔇 Silent | ❌ None |

### 8.3 Visual Architecture Map

The "City Map" view uses React Flow to show the application topology:

```typescript
// components/ArchitectureMap.tsx
import ReactFlow, { Node, Edge, Background, Controls } from 'reactflow';

interface ServiceNode {
  id: string;
  type: 'database' | 'api' | 'external' | 'cache';
  name: string;
  status: 'healthy' | 'warning' | 'critical';
  latency?: number;
  errorRate?: number;
}

const nodeStyles = {
  healthy: { background: '#10B981', border: '2px solid #059669' },
  warning: { background: '#F59E0B', border: '2px solid #D97706' },
  critical: { background: '#EF4444', border: '2px solid #DC2626' }
};

export function ArchitectureMap({ services }: { services: ServiceNode[] }) {
  const nodes: Node[] = services.map((service, index) => ({
    id: service.id,
    position: calculatePosition(index, services.length),
    data: {
      label: (
        <div className="flex items-center gap-2">
          <ServiceIcon type={service.type} />
          <span>{service.name}</span>
          <StatusIndicator status={service.status} />
        </div>
      )
    },
    style: nodeStyles[service.status]
  }));
  
  return (
    <ReactFlow nodes={nodes} edges={edges}>
      <Background />
      <Controls />
    </ReactFlow>
  );
}
```

### 8.4 Dashboard Mode Toggle

```typescript
// components/ModeToggle.tsx
type DashboardMode = 'developer' | 'auditor';

export function ModeToggle() {
  const [mode, setMode] = useState<DashboardMode>('developer');
  
  return (
    <div className="flex rounded-lg bg-gray-100 p-1">
      <button
        onClick={() => setMode('developer')}
        className={cn(
          "px-4 py-2 rounded-md transition",
          mode === 'developer' && "bg-white shadow"
        )}
      >
        👨‍💻 Developer
      </button>
      <button
        onClick={() => setMode('auditor')}
        className={cn(
          "px-4 py-2 rounded-md transition",
          mode === 'auditor' && "bg-white shadow"
        )}
      >
        📋 Auditor
      </button>
    </div>
  );
}
```

**Developer Mode Shows:**
- Real-time error stream
- "Fix this" code suggestions
- Performance metrics

**Auditor Mode Shows:**
- Deployment changelog
- Security scan history
- Uptime SLA reports
- Evidence export button

---

## 9. Deployment & Infrastructure

### 9.1 Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        CLOUDFLARE                           │
│                   (DNS + DDoS Protection)                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Vercel    │  │   Railway   │  │   Railway   │
│ (Dashboard) │  │ (API Primary)│ │(API Replica)│
│  Next.js    │  │   FastAPI   │  │   FastAPI   │
└─────────────┘  └──────┬──────┘  └──────┬──────┘
                        │                │
                        └────────┬───────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    Supabase     │  │   Upstash       │  │  OpenObserve    │
│   (Postgres)    │  │   (Redis)       │  │   (Logs)        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                                 │
                                 ▼
                     ┌─────────────────────┐
                     │  Cloudflare R2      │
                     │  (Evidence PDFs)    │
                     └─────────────────────┘
```

### 9.2 Environment Variables

```bash
# .env.example

# API Configuration
CODEWARDEN_ENV=production
CODEWARDEN_API_URL=https://api.codewarden.io

# Database
DATABASE_URL=postgresql://...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# Redis
REDIS_URL=redis://...
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...

# OpenObserve
OPENOBSERVE_URL=https://logs.codewarden.io
OPENOBSERVE_USER=admin@codewarden.io
OPENOBSERVE_PASSWORD=...

# AI Providers
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...

# Notifications
RESEND_API_KEY=re_...
TELEGRAM_BOT_TOKEN=...

# Storage
CLOUDFLARE_R2_ACCESS_KEY_ID=...
CLOUDFLARE_R2_SECRET_ACCESS_KEY=...
CLOUDFLARE_R2_BUCKET=codewarden-evidence
```

### 9.3 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest --cov

  deploy-api:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: railwayapp/railway-github-action@v1
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}

  deploy-dashboard:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

---

## 10. Development Phases

### Phase 1: MVP "The Crash Guard" (Weeks 1-4)

| Task | Priority | Owner | Status |
|------|----------|-------|--------|
| FastAPI middleware (Python SDK) | P0 | Backend | ⬜ |
| Airlock PII scrubber | P0 | Backend | ⬜ |
| Basic API endpoints | P0 | Backend | ⬜ |
| LiteLLM integration | P0 | Backend | ⬜ |
| Email notifications (Resend) | P0 | Backend | ⬜ |
| Terminal handshake flow | P1 | Backend | ⬜ |
| Basic dashboard (error list) | P1 | Frontend | ⬜ |
| pip-audit integration | P1 | Backend | ⬜ |

### Phase 2: "The Evidence Locker" (Weeks 5-8)

| Task | Priority | Owner | Status |
|------|----------|-------|--------|
| EvidenceCollector class | P0 | Backend | ⬜ |
| Deployment tracking | P0 | Backend | ⬜ |
| Security scan logging | P0 | Backend | ⬜ |
| Access event logging | P1 | Backend | ⬜ |
| SOC 2 PDF export | P1 | Backend | ⬜ |
| Compliance dashboard tab | P1 | Frontend | ⬜ |
| Telegram bot integration | P2 | Backend | ⬜ |

### Phase 3: "The Vibe Platform" (Weeks 9-16)

| Task | Priority | Owner | Status |
|------|----------|-------|--------|
| React Flow architecture map | P0 | Frontend | ⬜ |
| Next.js SDK | P0 | Frontend | ⬜ |
| Console Guard | P1 | Frontend | ⬜ |
| Network Spy | P1 | Frontend | ⬜ |
| Consensus Check (multi-model) | P2 | Backend | ⬜ |
| GitHub integration | P2 | Backend | ⬜ |
| Auditor Mode toggle | P2 | Frontend | ⬜ |

---

## 11. Testing Strategy

### 11.1 Unit Tests

```python
# tests/test_airlock.py
import pytest
from codewarden.scrubber import Airlock

class TestAirlock:
    def setup_method(self):
        self.airlock = Airlock()
    
    def test_scrubs_email(self):
        text = "User email is john@example.com"
        result = self.airlock.scrub(text)
        assert "[EMAIL_REDACTED]" in result
        assert "john@example.com" not in result
    
    def test_scrubs_credit_card(self):
        text = "Card: 4111-1111-1111-1111"
        result = self.airlock.scrub(text)
        assert "[CC_REDACTED]" in result
    
    def test_scrubs_api_keys(self):
        text = "key = sk-1234567890abcdefghijklmnopqrstuvwxyz123456"
        result = self.airlock.scrub(text)
        assert "[KEY_REDACTED]" in result
    
    def test_preserves_safe_text(self):
        text = "Normal log message without PII"
        result = self.airlock.scrub(text)
        assert result == text
```

### 11.2 Integration Tests

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from codewarden_api.main import app

client = TestClient(app)

def test_telemetry_endpoint():
    response = client.post(
        "/v1/telemetry",
        json={
            "source": "test",
            "type": "crash",
            "severity": "critical",
            "payload": {"error": "Test error"}
        },
        headers={"Authorization": "Bearer cw_test_xxx"}
    )
    assert response.status_code == 201
    assert "id" in response.json()

def test_invalid_api_key():
    response = client.post(
        "/v1/telemetry",
        json={},
        headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401
```

### 11.3 E2E Tests

```typescript
// tests/e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test('user can view error details', async ({ page }) => {
  await page.goto('/login');
  await page.fill('input[type="email"]', 'test@example.com');
  await page.click('button[type="submit"]');
  
  // Magic link flow simulation
  await page.goto('/verify?token=test-token');
  
  await expect(page).toHaveURL('/');
  await page.click('text=View Errors');
  
  await expect(page.locator('.error-card')).toBeVisible();
});
```

---

## 12. Appendix

### 12.1 Glossary

| Term | Definition |
|------|------------|
| **Airlock** | Client-side PII scrubbing module |
| **Evidence Locker** | SOC 2 compliance artifact storage |
| **WatchDog** | Main monitoring agent |
| **Consensus Check** | Multi-model AI verification |
| **OTel** | OpenTelemetry standard |

### 12.2 References

- [OpenTelemetry Specification](https://opentelemetry.io/docs/specs/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [pip-audit GitHub](https://github.com/pypa/pip-audit)
- [Gitleaks Patterns](https://github.com/gitleaks/gitleaks)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [React Flow Documentation](https://reactflow.dev/)

---

**Document Control:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2026 | Engineering Team | Initial release |
