# CodeWarden System Design Document

**Document Version:** 1.0  
**Status:** Approved for Development  
**Last Updated:** January 2026  
**Owner:** Engineering Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Design Philosophy](#2-design-philosophy)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Layer 1: The Edge](#4-layer-1-the-edge)
5. [Layer 2: The Gateway](#5-layer-2-the-gateway)
6. [Layer 3: The Brain](#6-layer-3-the-brain)
7. [Layer 4: The Vault](#7-layer-4-the-vault)
8. [Technology Decisions](#8-technology-decisions)
9. [Monorepo Strategy](#9-monorepo-strategy)
10. [Data Flow Architecture](#10-data-flow-architecture)
11. [Deployment Architecture](#11-deployment-architecture)
12. [Security Architecture](#12-security-architecture)
13. [Scalability & Performance](#13-scalability--performance)
14. [Disaster Recovery](#14-disaster-recovery)
15. [Development Environment](#15-development-environment)

---

## 1. Executive Summary

### 1.1 Purpose

This document defines the complete system architecture for CodeWarden, a security and observability platform for solopreneurs. It serves as the authoritative reference for all engineering decisions, infrastructure choices, and technical implementation details.

### 1.2 Architecture Overview

CodeWarden employs a **4-Layer "Hub & Spoke" Architecture** designed around three core principles:

1. **Privacy-First:** All PII scrubbing happens client-side before data transmission
2. **Model-Agnostic:** AI providers can be switched instantly without code changes
3. **Acquisition-Ready:** OpenTelemetry-native data formats for enterprise compatibility

### 1.3 Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | Supabase (Postgres) | Managed reliability, built-in auth, metadata storage |
| Log Storage | OpenObserve | 140x cheaper than Splunk, SOC 2 compliant |
| AI Router | LiteLLM | Provider-agnostic, automatic failover |
| Repository | Monorepo | Atomic updates, unified dev environment |
| Queue | Redis + ARQ | Simple async processing, Python-native |

---

## 2. Design Philosophy

### 2.1 Core Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                     DESIGN PRINCIPLES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │  FAIL-OPEN  │   │   PRIVACY   │   │    MODEL    │           │
│  │             │   │    FIRST    │   │  AGNOSTIC   │           │
│  │ If we break,│   │ Data stays  │   │ Switch AI   │           │
│  │ user's app  │   │ on user's   │   │ providers   │           │
│  │ keeps running│   │ server      │   │ instantly   │           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │    OTEL     │   │   COST      │   │   SIMPLE    │           │
│  │   NATIVE    │   │  OPTIMIZED  │   │   FIRST     │           │
│  │ Enterprise- │   │ OpenObserve │   │ Zero-config │           │
│  │ compatible  │   │ not Splunk  │   │ defaults    │           │
│  │ data format │   │             │   │             │           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Fail-Open Strategy

CodeWarden must never break the user's application. Every component is designed to fail gracefully:

| Component | Failure Mode | User Impact |
|-----------|--------------|-------------|
| SDK Middleware | Catches exception, continues | Zero - app runs normally |
| API Gateway | Returns 503, SDK retries | Alerts delayed, not lost |
| AI Analysis | Falls back to next provider | Analysis continues |
| Log Storage | Buffers locally, retries | Logs eventually delivered |
| Dashboard | Shows cached data | Stale but functional |

### 2.3 "No Weak Links" Architecture

A "weak link" is any single point of failure that kills the business. We eliminate these through redundancy:

```
                    WEAK LINK ELIMINATION
                    
   Single AI Provider          →    LiteLLM Multi-Provider
   ┌─────────┐                      ┌─────────┐
   │ Gemini  │ (if down, dead)      │ Gemini  │──┐
   └─────────┘                      ├─────────┤  │ Auto-
                                    │ Claude  │──┤ Failover
                                    ├─────────┤  │
                                    │ GPT-4o  │──┘
                                    └─────────┘
   
   Single Database              →    Separated by Purpose
   ┌─────────┐                      ┌─────────┐
   │ One DB  │ (overloaded)         │Supabase │ Metadata
   └─────────┘                      ├─────────┤
                                    │OpenObserve│ Logs
                                    ├─────────┤
                                    │  R2/S3  │ Artifacts
                                    └─────────┘
```

---

## 3. High-Level Architecture

### 3.1 The 4-Layer "Hub & Spoke" Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                         LAYER 1: THE EDGE                               │
│                    (User's Infrastructure - Client-Side)                │
│                                                                         │
│    ┌────────────────────────┐      ┌────────────────────────┐          │
│    │     codewarden-py      │      │     codewarden-js      │          │
│    │     (Python Agent)     │      │    (Node.js Agent)     │          │
│    │                        │      │                        │          │
│    │  ┌──────────────────┐  │      │  ┌──────────────────┐  │          │
│    │  │    Middleware    │  │      │  │  Instrumentation │  │          │
│    │  │  (FastAPI/Flask) │  │      │  │    (Next.js)     │  │          │
│    │  └────────┬─────────┘  │      │  └────────┬─────────┘  │          │
│    │           │            │      │           │            │          │
│    │  ┌────────▼─────────┐  │      │  ┌────────▼─────────┐  │          │
│    │  │     Airlock      │  │      │  │   Console Guard  │  │          │
│    │  │  (PII Scrubber)  │  │      │  │   Network Spy    │  │          │
│    │  └────────┬─────────┘  │      │  └────────┬─────────┘  │          │
│    │           │            │      │           │            │          │
│    │  ┌────────▼─────────┐  │      │  ┌────────▼─────────┐  │          │
│    │  │   Vuln Scanner   │  │      │  │  Error Boundary  │  │          │
│    │  │   (pip-audit)    │  │      │  │     (React)      │  │          │
│    │  └────────┬─────────┘  │      │  └────────┬─────────┘  │          │
│    │           │            │      │           │            │          │
│    └───────────┼────────────┘      └───────────┼────────────┘          │
│                │                               │                        │
│                └───────────────┬───────────────┘                        │
│                                │                                        │
│                         HTTPS (TLS 1.3)                                 │
│                      Scrubbed Data Only                                 │
│                                │                                        │
└────────────────────────────────┼────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│                         LAYER 2: THE GATEWAY                           │
│                           (Our API Server)                             │
│                                                                        │
│    ┌────────────────────────────────────────────────────────────┐     │
│    │                    CLOUDFLARE (Edge)                        │     │
│    │              DDoS Protection · WAF · Rate Limiting          │     │
│    └────────────────────────────┬───────────────────────────────┘     │
│                                 │                                      │
│    ┌────────────────────────────▼───────────────────────────────┐     │
│    │                  FastAPI Ingestion Service                  │     │
│    │                      (Railway × 2)                          │     │
│    │                                                             │     │
│    │   POST /v1/telemetry    ─── Error/Log Ingestion            │     │
│    │   POST /v1/evidence     ─── Compliance Events              │     │
│    │   GET  /v1/health       ─── SDK Health Check               │     │
│    │   POST /v1/pairing/*    ─── Device Pairing                 │     │
│    │                                                             │     │
│    └────────────────────────────┬───────────────────────────────┘     │
│                                 │                                      │
│    ┌────────────────────────────▼───────────────────────────────┐     │
│    │                   Redis + ARQ Job Queue                     │     │
│    │                       (Upstash)                             │     │
│    │                                                             │     │
│    │   • Async log processing (non-blocking)                     │     │
│    │   • Rate limit counters                                     │     │
│    │   • Session/pairing state                                   │     │
│    │   • Job retry with exponential backoff                      │     │
│    │                                                             │     │
│    └────────────────────────────┬───────────────────────────────┘     │
│                                 │                                      │
└─────────────────────────────────┼──────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                          LAYER 3: THE BRAIN                             │
│                        (AI Analysis Engine)                             │
│                                                                         │
│    ┌───────────────────────────────────────────────────────────────┐   │
│    │                       LiteLLM Router                           │   │
│    │                                                                │   │
│    │    ┌─────────────────────────────────────────────────────┐    │   │
│    │    │                   ROUTING LOGIC                      │    │   │
│    │    │                                                      │    │   │
│    │    │   Simple Query ───────▶ Gemini Flash (Fast/Cheap)   │    │   │
│    │    │   Complex Debug ──────▶ Claude Sonnet (Smart)       │    │   │
│    │    │   Provider Down ──────▶ GPT-4o Mini (Fallback)      │    │   │
│    │    │   Critical Alert ─────▶ ALL THREE (Consensus)       │    │   │
│    │    │                                                      │    │   │
│    │    └─────────────────────────────────────────────────────┘    │   │
│    │                                                                │   │
│    │    ┌──────────┐    ┌──────────┐    ┌──────────┐               │   │
│    │    │  Gemini  │    │  Claude  │    │  GPT-4o  │               │   │
│    │    │  Flash   │    │  Sonnet  │    │   Mini   │               │   │
│    │    │          │    │          │    │          │               │   │
│    │    │  $0.075  │    │  $3.00   │    │  $0.15   │               │   │
│    │    │  /1M tok │    │  /1M tok │    │  /1M tok │               │   │
│    │    └──────────┘    └──────────┘    └──────────┘               │   │
│    │                                                                │   │
│    └───────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                          LAYER 4: THE VAULT                             │
│                        (Storage & Persistence)                          │
│                                                                         │
│    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐           │
│    │               │   │               │   │               │           │
│    │   SUPABASE    │   │  OPENOBSERVE  │   │  CLOUDFLARE   │           │
│    │   (Postgres)  │   │    (Rust)     │   │      R2       │           │
│    │               │   │               │   │               │           │
│    │  ┌─────────┐  │   │  ┌─────────┐  │   │  ┌─────────┐  │           │
│    │  │ Users   │  │   │  │  Logs   │  │   │  │Evidence │  │           │
│    │  │ Apps    │  │   │  │ Traces  │  │   │  │  PDFs   │  │           │
│    │  │ Billing │  │   │  │ Metrics │  │   │  │ Exports │  │           │
│    │  │ Config  │  │   │  │  Spans  │  │   │  │ Backups │  │           │
│    │  └─────────┘  │   │  └─────────┘  │   │  └─────────┘  │           │
│    │               │   │               │   │               │           │
│    │  Auth/Magic   │   │  140x cheaper │   │  S3-compat    │           │
│    │  Link Built-in│   │  than Splunk  │   │  Zero egress  │           │
│    │               │   │               │   │               │           │
│    └───────────────┘   └───────────────┘   └───────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Request Flow Summary

```
User's App (FastAPI)
       │
       │ 1. Error occurs
       ▼
┌──────────────────┐
│ codewarden-py    │
│   Middleware     │
└────────┬─────────┘
         │ 2. Catches error
         ▼
┌──────────────────┐
│     Airlock      │
│  (PII Scrubber)  │
└────────┬─────────┘
         │ 3. Scrubs sensitive data
         ▼
┌──────────────────┐
│   HTTPS POST     │
│  to Gateway API  │
└────────┬─────────┘
         │ 4. Sends to CodeWarden
         ▼
┌──────────────────┐
│   FastAPI        │
│   Gateway        │
└────────┬─────────┘
         │ 5. Queues for processing
         ▼
┌──────────────────┐
│   Redis + ARQ    │
│   Job Queue      │
└────────┬─────────┘
         │ 6. Async worker picks up
         ▼
┌──────────────────┐
│   LiteLLM        │
│   AI Analysis    │
└────────┬─────────┘
         │ 7. Generates explanation
         ▼
┌──────────────────┐         ┌──────────────────┐
│   OpenObserve    │         │    Supabase      │
│   (Store Log)    │         │ (Update Metadata)│
└──────────────────┘         └────────┬─────────┘
                                      │ 8. Trigger notification
                                      ▼
                             ┌──────────────────┐
                             │  Resend/Telegram │
                             │   Notification   │
                             └──────────────────┘
                                      │
                                      ▼
                                   📧 User
```

---

## 4. Layer 1: The Edge

### 4.1 Overview

The Edge layer runs inside the user's infrastructure. It is responsible for:

1. **Intercepting** requests, responses, and errors
2. **Scrubbing** PII before any data leaves the server
3. **Scanning** for vulnerabilities on startup
4. **Buffering** data if the Gateway is unreachable

### 4.2 Python Agent (`codewarden-py`)

```
codewarden-py/
├── codewarden/
│   ├── __init__.py           # Main CodeWarden class
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── fastapi.py        # FastAPI middleware
│   │   ├── flask.py          # Flask middleware (Phase 2)
│   │   └── django.py         # Django middleware (Phase 2)
│   ├── scrubber/
│   │   ├── __init__.py
│   │   ├── airlock.py        # Main PII scrubbing engine
│   │   ├── patterns.py       # Regex patterns (Gitleaks-based)
│   │   └── sanitizer.py      # Log sanitization utilities
│   ├── scanner/
│   │   ├── __init__.py
│   │   ├── dependencies.py   # pip-audit wrapper
│   │   ├── secrets.py        # Secret detection in env vars
│   │   └── code.py           # Bandit integration
│   ├── evidence/
│   │   ├── __init__.py
│   │   ├── collector.py      # EvidenceCollector class
│   │   ├── deploy.py         # Deployment tracking
│   │   └── access.py         # Access logging
│   ├── transport/
│   │   ├── __init__.py
│   │   ├── client.py         # HTTPS client with retry
│   │   └── buffer.py         # Local buffer for offline mode
│   ├── notifier/
│   │   ├── __init__.py
│   │   ├── email.py          # Resend integration
│   │   └── telegram.py       # Telegram bot integration
│   ├── handshake/
│   │   ├── __init__.py
│   │   ├── setup.py          # Terminal pairing experience
│   │   ├── telegram.py       # Telegram pairing flow
│   │   └── email.py          # Email magic link pairing
│   └── config.py             # Configuration management
├── tests/
├── pyproject.toml
└── README.md
```

#### 4.2.1 Middleware Architecture

```python
# Middleware intercepts ALL HTTP traffic
class CodeWardenMiddleware(BaseHTTPMiddleware):
    """
    Non-blocking middleware that:
    1. Generates trace IDs for request correlation
    2. Measures request latency
    3. Catches unhandled exceptions
    4. Scrubs and forwards to Gateway
    """
    
    async def dispatch(self, request, call_next):
        trace_id = self.generate_trace_id()
        start_time = time.time()
        
        try:
            response = await call_next(request)
            self.log_request(trace_id, request, response, start_time)
            return response
            
        except Exception as e:
            # CRITICAL: Re-raise after logging
            # User's app must continue to handle error normally
            self.report_error(trace_id, request, e)
            raise
```

#### 4.2.2 Airlock (PII Scrubber)

The Airlock is the heart of our privacy-first architecture. It runs **client-side** and ensures no sensitive data ever leaves the user's server.

```python
class Airlock:
    """
    Client-side PII scrubbing engine.
    Patterns derived from Gitleaks (open source).
    """
    
    PATTERNS = {
        # Identity
        'EMAIL': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'PHONE': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'SSN': r'\b\d{3}-\d{2}-\d{4}\b',
        
        # Financial
        'CREDIT_CARD': r'\b(?:\d{4}[- ]?){3}\d{4}\b',
        
        # API Keys (provider-specific patterns)
        'API_KEY_OPENAI': r'sk-[a-zA-Z0-9]{48}',
        'API_KEY_STRIPE': r'sk_(live|test)_[a-zA-Z0-9]{24,}',
        'API_KEY_AWS': r'AKIA[0-9A-Z]{16}',
        'API_KEY_GOOGLE': r'AIza[0-9A-Za-z\-_]{35}',
        
        # Auth Tokens
        'JWT': r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+',
        'PASSWORD_FIELD': r'(?i)(password|passwd|pwd)\s*[:=]\s*\S+',
    }
    
    REPLACEMENTS = {
        'EMAIL': '[EMAIL_REDACTED]',
        'CREDIT_CARD': '[CC_REDACTED]',
        'API_KEY_*': '[KEY_REDACTED]',
        # ... etc
    }
```

**Scrubbing Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│                    AIRLOCK SCRUBBING FLOW                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Raw Error Log                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ User john@example.com failed payment with           │   │
│  │ card 4111-1111-1111-1111 using key sk_live_xxx...   │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Pattern Matching Engine                 │   │
│  │                                                      │   │
│  │  EMAIL_REGEX.match() ───▶ john@example.com          │   │
│  │  CREDIT_CARD_REGEX.match() ───▶ 4111-1111-1111-1111 │   │
│  │  API_KEY_STRIPE.match() ───▶ sk_live_xxx...         │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  Scrubbed Log (Safe for Transmission)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ User [EMAIL_REDACTED] failed payment with           │   │
│  │ card [CC_REDACTED] using key [KEY_REDACTED]         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 JavaScript Agent (`codewarden-js`)

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
│   │   ├── airlock.ts        # PII scrubbing (JS port)
│   │   └── patterns.ts       # Regex patterns
│   ├── transport/
│   │   ├── client.ts         # API client
│   │   └── buffer.ts         # IndexedDB buffer
│   └── types/
│       └── index.ts          # TypeScript definitions
├── package.json
└── tsconfig.json
```

#### 4.3.1 Console Guard

Prevents accidental secret leakage in browser console:

```typescript
class ConsoleGuard {
    private originalConsole: typeof console;
    
    install(): void {
        if (process.env.NODE_ENV !== 'production') return;
        
        this.originalConsole = { ...console };
        
        // Override console methods
        ['log', 'warn', 'error', 'info'].forEach(method => {
            console[method] = (...args) => {
                const scrubbed = args.map(arg => 
                    typeof arg === 'string' 
                        ? this.airlock.scrub(arg) 
                        : arg
                );
                
                // Check for secrets BEFORE logging
                if (this.containsSecrets(args)) {
                    this.reportLeak(method, args);
                    return; // Don't log at all
                }
                
                this.originalConsole[method](...scrubbed);
            };
        });
    }
}
```

#### 4.3.2 Network Spy

Monitors failed API requests:

```typescript
class NetworkSpy {
    install(): void {
        const originalFetch = window.fetch;
        
        window.fetch = async (...args) => {
            const startTime = performance.now();
            
            try {
                const response = await originalFetch(...args);
                
                if (!response.ok) {
                    this.reportFailure({
                        url: args[0],
                        status: response.status,
                        duration: performance.now() - startTime
                    });
                }
                
                return response;
            } catch (error) {
                this.reportNetworkError({
                    url: args[0],
                    error: error.message,
                    duration: performance.now() - startTime
                });
                throw error;
            }
        };
    }
}
```

---

## 5. Layer 2: The Gateway

### 5.1 Overview

The Gateway is our centralized API that receives scrubbed data from Edge agents. It is designed for:

1. **High Availability:** Multiple Railway instances behind Cloudflare
2. **Non-Blocking:** All heavy processing is queued
3. **Rate Limited:** Protects against abuse and runaway SDKs

### 5.2 API Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           GATEWAY ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      CLOUDFLARE EDGE                             │   │
│  │                                                                  │   │
│  │   • DDoS Protection (Always-on)                                 │   │
│  │   • WAF Rules (Block malicious patterns)                        │   │
│  │   • Rate Limiting (1000 req/min/IP)                             │   │
│  │   • Geographic Routing (Nearest datacenter)                      │   │
│  │   • SSL Termination (TLS 1.3)                                   │   │
│  │                                                                  │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      LOAD BALANCER                                │  │
│  │                    (Railway Internal)                             │  │
│  └─────────┬────────────────────────────────────────┬───────────────┘  │
│            │                                        │                   │
│            ▼                                        ▼                   │
│  ┌──────────────────┐                    ┌──────────────────┐          │
│  │   API Instance   │                    │   API Instance   │          │
│  │   (Primary)      │                    │   (Replica)      │          │
│  │                  │                    │                  │          │
│  │   FastAPI        │                    │   FastAPI        │          │
│  │   Python 3.11    │                    │   Python 3.11    │          │
│  │   Uvicorn        │                    │   Uvicorn        │          │
│  │                  │                    │                  │          │
│  └────────┬─────────┘                    └────────┬─────────┘          │
│           │                                       │                     │
│           └───────────────────┬───────────────────┘                     │
│                               │                                         │
│                               ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                         UPSTASH REDIS                             │  │
│  │                                                                   │  │
│  │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐            │  │
│  │   │  Job Queue  │   │Rate Limits  │   │   Session   │            │  │
│  │   │   (ARQ)     │   │  Counters   │   │    Store    │            │  │
│  │   └─────────────┘   └─────────────┘   └─────────────┘            │  │
│  │                                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.3 API Endpoints

```python
# api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CodeWarden API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None
)

# ─────────────────────────────────────────────────────────────
# TELEMETRY ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.post("/v1/telemetry", status_code=201)
async def ingest_telemetry(
    payload: TelemetryPayload,
    api_key: str = Depends(verify_api_key),
    redis: Redis = Depends(get_redis)
):
    """
    Receives scrubbed error/log data from SDKs.
    Immediately queues for async processing.
    """
    # 1. Validate payload
    if not payload.trace_scrubbed:
        raise HTTPException(400, "Payload must be scrubbed")
    
    # 2. Generate event ID
    event_id = f"evt_{generate_id()}"
    
    # 3. Queue for processing (non-blocking)
    await redis.enqueue(
        "process_telemetry",
        event_id=event_id,
        app_id=api_key.app_id,
        payload=payload.dict()
    )
    
    # 4. Return immediately
    return {"id": event_id, "status": "queued"}


@app.post("/v1/evidence")
async def log_evidence(
    payload: EvidencePayload,
    api_key: str = Depends(verify_api_key)
):
    """
    Logs compliance-relevant events for SOC 2.
    Stored directly (no AI processing needed).
    """
    await supabase.table("evidence_events").insert({
        "app_id": api_key.app_id,
        "event_type": payload.type,
        "data": payload.data,
        "created_at": datetime.utcnow()
    })
    
    return {"status": "logged"}


# ─────────────────────────────────────────────────────────────
# PAIRING ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.post("/v1/pairing/telegram")
async def initiate_telegram_pairing(code: str):
    """Generate a pairing code for Telegram verification."""
    pairing_code = f"CW-{random.randint(1000, 9999)}"
    await redis.setex(f"pairing:{pairing_code}", 300, "pending")
    return {"code": pairing_code, "expires_in": 300}


@app.post("/v1/pairing/email")
async def initiate_email_pairing(email: str):
    """Send magic link for email verification."""
    token = generate_secure_token()
    await redis.setex(f"magic:{token}", 3600, email)
    await send_magic_link_email(email, token)
    return {"status": "sent"}


@app.get("/v1/pairing/status")
async def check_pairing_status(identifier: str, method: str):
    """Poll endpoint for pairing verification status."""
    if method == "telegram":
        status = await redis.get(f"pairing:{identifier}")
    else:
        status = await redis.get(f"magic:{identifier}")
    
    return {"verified": status == "verified"}


# ─────────────────────────────────────────────────────────────
# HEALTH & UTILITY ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/v1/health")
async def health_check(api_key: str = Depends(verify_api_key)):
    """SDK health check and configuration sync."""
    app = await supabase.table("apps").select("*").eq("api_key", api_key).single()
    
    return {
        "status": "healthy",
        "app": {
            "id": app["id"],
            "name": app["name"],
            "plan": app["plan"]
        },
        "config": app["config"]
    }
```

### 5.4 Job Queue (ARQ)

```python
# api/workers/processor.py
import arq
from litellm import acompletion

async def process_telemetry(ctx, event_id: str, app_id: str, payload: dict):
    """
    Async worker that:
    1. Analyzes the error with AI
    2. Stores in OpenObserve
    3. Updates metadata in Supabase
    4. Triggers notifications
    """
    
    # 1. AI Analysis
    analysis = await analyze_error(payload)
    
    # 2. Store log in OpenObserve
    await openobserve.ingest(
        stream="errors",
        data={
            "event_id": event_id,
            "app_id": app_id,
            "error": payload["error"],
            "analysis": analysis,
            "timestamp": payload["timestamp"]
        }
    )
    
    # 3. Update metadata
    await supabase.table("event_metadata").insert({
        "id": event_id,
        "app_id": app_id,
        "event_type": payload["type"],
        "severity": analysis["severity"],
        "analysis_result": analysis
    })
    
    # 4. Send notification if critical
    if analysis["severity"] == "critical":
        await send_notification(app_id, event_id, analysis)


class WorkerSettings:
    functions = [process_telemetry]
    redis_settings = arq.RedisSettings.from_dsn(REDIS_URL)
    max_jobs = 100
    job_timeout = 60
```

---

## 6. Layer 3: The Brain

### 6.1 Overview

The Brain layer handles all AI-powered analysis. It is designed to be:

1. **Provider-Agnostic:** Switch between Gemini, Claude, GPT with one config change
2. **Cost-Optimized:** Route simple queries to cheap models, complex to smart
3. **Highly Available:** Automatic failover if any provider goes down

### 6.2 LiteLLM Router

```python
# api/brain/router.py
from litellm import completion, acompletion
from enum import Enum

class AnalysisMode(Enum):
    FAST = "fast"      # Gemini Flash - cheap, quick
    SMART = "smart"    # Claude Sonnet - best reasoning
    FALLBACK = "fallback"  # GPT-4o Mini - reliable backup

class AIRouter:
    """
    Model-agnostic AI router using LiteLLM.
    Handles routing, failover, and cost optimization.
    """
    
    MODEL_CONFIG = {
        AnalysisMode.FAST: {
            "model": "gemini/gemini-1.5-flash",
            "max_tokens": 1000,
            "temperature": 0.3,
            "cost_per_1m_tokens": 0.075
        },
        AnalysisMode.SMART: {
            "model": "anthropic/claude-3-5-sonnet-20241022",
            "max_tokens": 2000,
            "temperature": 0.2,
            "cost_per_1m_tokens": 3.00
        },
        AnalysisMode.FALLBACK: {
            "model": "openai/gpt-4o-mini",
            "max_tokens": 1000,
            "temperature": 0.3,
            "cost_per_1m_tokens": 0.15
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
        mode: AnalysisMode = AnalysisMode.FAST
    ) -> dict:
        """Analyze error with automatic failover."""
        
        config = self.MODEL_CONFIG[mode]
        fallback_config = self.MODEL_CONFIG[AnalysisMode.FALLBACK]
        
        try:
            response = await acompletion(
                model=config["model"],
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": self._format_error(error_data)}
                ],
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                # LiteLLM auto-fallback
                fallbacks=[fallback_config["model"]]
            )
            
            return self._parse_response(response)
            
        except Exception as e:
            # Ultimate fallback: Return basic info
            return {
                "summary": f"Error occurred: {error_data.get('error_type')}",
                "root_cause": "Analysis temporarily unavailable",
                "fix_suggestion": "Please check the dashboard",
                "severity": "unknown",
                "analysis_error": str(e)
            }
```

### 6.3 Consensus Check (Multi-Model Verification)

For critical security alerts, we don't trust a single AI. We run parallel queries:

```python
# api/brain/consensus.py
import asyncio
from collections import Counter

class ConsensusChecker:
    """
    Run the same prompt through multiple models.
    Use majority vote for critical decisions.
    """
    
    async def check(self, payload: dict) -> dict:
        """
        Returns consensus verdict from 3 models.
        Used for: SQL injection detection, XSS detection, etc.
        """
        
        prompt = self._build_security_prompt(payload)
        
        # Fire all 3 models simultaneously
        tasks = [
            acompletion(model="gemini/gemini-1.5-flash", messages=[...]),
            acompletion(model="anthropic/claude-3-5-sonnet", messages=[...]),
            acompletion(model="openai/gpt-4o", messages=[...])
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Extract verdicts (SAFE / ATTACK / UNCERTAIN)
        verdicts = []
        for result in results:
            if not isinstance(result, Exception):
                verdict = self._extract_verdict(result)
                verdicts.append(verdict)
        
        # Majority vote
        vote_counts = Counter(verdicts)
        winner, count = vote_counts.most_common(1)[0]
        
        return {
            "verdict": winner,
            "confidence": count / len(verdicts),
            "models_agreed": count,
            "models_total": len(verdicts),
            "individual_verdicts": verdicts
        }
```

**Consensus Example:**

```
┌─────────────────────────────────────────────────────────────┐
│                    CONSENSUS CHECK EXAMPLE                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input: Suspicious log pattern detected                     │
│  Query: "SELECT * FROM users WHERE id = '1; DROP TABLE--"   │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Gemini  │  │  Claude  │  │  GPT-4o  │                  │
│  │  Flash   │  │  Sonnet  │  │          │                  │
│  ├──────────┤  ├──────────┤  ├──────────┤                  │
│  │  SAFE    │  │  ATTACK  │  │  ATTACK  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│       │             │             │                         │
│       └─────────────┴─────────────┘                         │
│                     │                                       │
│                     ▼                                       │
│            ┌─────────────────┐                              │
│            │  MAJORITY VOTE  │                              │
│            │                 │                              │
│            │  ATTACK (2/3)   │                              │
│            │  Confidence: 67%│                              │
│            └─────────────────┘                              │
│                     │                                       │
│                     ▼                                       │
│         🚨 Alert User: "SQL Injection Detected"             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Layer 4: The Vault

### 7.1 Overview

The Vault handles all persistent storage. It is split into specialized stores to optimize for different access patterns and costs.

### 7.2 Why Supabase?

Supabase was selected as the metadata database for three primary reasons:

| Reason | Details |
|--------|---------|
| **Managed Reliability** | Automatic nightly backups, point-in-time recovery, no DevOps overhead |
| **Authentication Built-in** | Magic Link (passwordless) auth works out of the box |
| **Metadata Focus** | Perfect for user accounts, app configs, billing - not for high-volume logs |

**What Supabase Stores:**

```sql
-- Users and authentication
users (id, email, org_id, notification_prefs, created_at)

-- Applications registered with CodeWarden
apps (id, org_id, name, api_key, config, last_seen_at)

-- Event metadata (pointers to logs in OpenObserve)
event_metadata (id, app_id, event_type, severity, openobserve_id, analysis_result)

-- Compliance evidence
evidence_events (id, app_id, event_type, data, created_at)

-- Billing and subscriptions
subscriptions (id, org_id, plan, status, stripe_id)
```

**What Supabase Does NOT Store:**

- Raw logs (→ OpenObserve)
- Traces and spans (→ OpenObserve)
- Large binary files (→ R2/S3)
- High-frequency metrics (→ OpenObserve)

### 7.3 OpenObserve (Log Storage)

OpenObserve is a Rust-based observability platform that is **140x cheaper than Splunk**.

**Why OpenObserve:**

| Factor | OpenObserve | Splunk | Datadog |
|--------|-------------|--------|---------|
| Cost (1TB/mo) | ~$50 | ~$7,000 | ~$3,000 |
| Self-hostable | ✅ Yes | ❌ No | ❌ No |
| SOC 2 Compliant | ✅ Yes | ✅ Yes | ✅ Yes |
| OpenTelemetry | ✅ Native | ⚠️ Plugin | ✅ Native |

**OpenObserve Schema:**

```json
// Stream: errors
{
  "event_id": "evt_abc123",
  "app_id": "app_xyz789",
  "timestamp": "2026-01-04T10:00:00Z",
  "severity": "critical",
  "error_type": "ZeroDivisionError",
  "error_message": "division by zero",
  "file": "services/pricing.py",
  "line": 45,
  "trace_scrubbed": "Traceback (most recent call last)...",
  "analysis": {
    "summary": "Your pricing calculation crashed...",
    "fix_code": "..."
  }
}

// Stream: access_logs
{
  "timestamp": "2026-01-04T10:00:00Z",
  "app_id": "app_xyz789",
  "user_id": "user_123",
  "action": "login",
  "resource": "/admin/settings",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}

// Stream: metrics
{
  "timestamp": "2026-01-04T10:00:00Z",
  "app_id": "app_xyz789",
  "metric": "request_latency_ms",
  "value": 245,
  "tags": {
    "endpoint": "/api/checkout",
    "method": "POST"
  }
}
```

### 7.4 Cloudflare R2 (Artifact Storage)

R2 is used for large, infrequently-accessed files:

| Use Case | Example |
|----------|---------|
| SOC 2 Evidence PDFs | `evidence/org_123/soc2_2025.pdf` |
| Audit Exports | `exports/exp_abc/evidence_package.zip` |
| Backup Archives | `backups/2026-01-04/supabase_dump.sql.gz` |

**Why R2 over S3:**

- Zero egress fees (S3 charges for downloads)
- S3-compatible API (drop-in replacement)
- Cloudflare network = fast global delivery

### 7.5 Storage Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         VAULT LAYER ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                          WRITE PATH                              │   │
│  │                                                                  │   │
│  │   Telemetry ────▶ OpenObserve (high volume, append-only)        │   │
│  │   Metadata ─────▶ Supabase (low volume, transactional)          │   │
│  │   Artifacts ────▶ R2 (large files, infrequent writes)           │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                          READ PATH                               │   │
│  │                                                                  │   │
│  │   Dashboard ────▶ Supabase (user context, app list)             │   │
│  │              ────▶ OpenObserve (error logs, traces)             │   │
│  │                                                                  │   │
│  │   Evidence  ────▶ R2 (PDF downloads)                            │   │
│  │   Export                                                         │   │
│  │                                                                  │   │
│  │   SDK Health ───▶ Supabase (config sync)                        │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        DATA LIFECYCLE                            │   │
│  │                                                                  │   │
│  │   Hot Data (< 7 days)                                           │   │
│  │   ├── OpenObserve RAM cache                                     │   │
│  │   └── Fast queries, real-time dashboards                        │   │
│  │                                                                  │   │
│  │   Warm Data (7-90 days)                                         │   │
│  │   ├── OpenObserve disk storage                                  │   │
│  │   └── Slightly slower queries, historical analysis              │   │
│  │                                                                  │   │
│  │   Cold Data (> 90 days)                                         │   │
│  │   ├── R2 archived exports                                       │   │
│  │   └── Compliance retention only                                 │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Technology Decisions

### 8.1 Technology Stack Summary

| Layer | Component | Technology | Rationale |
|-------|-----------|------------|-----------|
| **Edge** | Python SDK | Python 3.11+ | Target audience uses FastAPI/Flask |
| **Edge** | JS SDK | TypeScript | Next.js ecosystem |
| **Edge** | PII Scrubbing | Regex (Gitleaks) | No dependencies, fast, proven |
| **Edge** | Vuln Scanning | pip-audit, npm audit | Official tools, OSV database |
| **Gateway** | API Server | FastAPI | Async, fast, Python AI ecosystem |
| **Gateway** | Hosting | Railway | Simple deploys, auto-scaling |
| **Gateway** | CDN/WAF | Cloudflare | DDoS protection, global edge |
| **Gateway** | Queue | Redis + ARQ | Simple, Python-native async |
| **Gateway** | Redis Host | Upstash | Serverless, pay-per-use |
| **Brain** | AI Router | LiteLLM | Provider-agnostic, failover |
| **Brain** | Fast Model | Gemini Flash | Cheap ($0.075/1M tokens) |
| **Brain** | Smart Model | Claude Sonnet | Best reasoning |
| **Brain** | Fallback | GPT-4o Mini | Reliable, always available |
| **Vault** | Metadata DB | Supabase | Managed Postgres, auth built-in |
| **Vault** | Log Storage | OpenObserve | 140x cheaper than Splunk |
| **Vault** | Artifacts | Cloudflare R2 | Zero egress, S3-compatible |
| **Dashboard** | Framework | Next.js 14 | React, Vercel-native |
| **Dashboard** | Hosting | Vercel | Edge deployment, instant deploys |
| **Dashboard** | State | TanStack Query | Caching, real-time updates |
| **Dashboard** | Visualizations | React Flow | Interactive architecture diagrams |
| **Notifications** | Email | Resend | Developer-friendly, reliable |
| **Notifications** | Mobile | Telegram Bot | Instant, rich formatting |

### 8.2 Why NOT Other Technologies

| Rejected | Chosen | Reason |
|----------|--------|--------|
| MongoDB | Postgres (Supabase) | Relational queries for billing, better tooling |
| Elasticsearch | OpenObserve | 140x cheaper, OTel-native |
| AWS S3 | Cloudflare R2 | Zero egress fees |
| Celery | ARQ | Simpler, async-native, less overhead |
| Direct OpenAI | LiteLLM | Multi-provider support, failover |
| Express.js | FastAPI | Better async, Python AI ecosystem |
| Firebase | Supabase | Open source, Postgres flexibility |

---

## 9. Monorepo Strategy

### 9.1 Why Monorepo?

CodeWarden uses a **monorepo** strategy for three critical reasons:

| Reason | Explanation |
|--------|-------------|
| **Simplified Management** | Single Git repo containing API, Dashboard, and SDKs. One place to manage issues, PRs, and CI/CD. |
| **Unified Development Environment** | Single `docker-compose.yml` spins up entire ecosystem for local testing. |
| **Atomic Updates** | Changes to log schemas affect SDK → API → Dashboard. Monorepo ensures these ship together. |

### 9.2 Repository Structure

```
codewarden/
│
├── README.md                     # Project overview
├── LICENSE                       # MIT License
├── docker-compose.yml            # Local dev environment
├── .github/
│   ├── workflows/
│   │   ├── ci.yml               # Test all packages
│   │   ├── deploy-api.yml       # Deploy API to Railway
│   │   ├── deploy-dashboard.yml # Deploy Dashboard to Vercel
│   │   └── publish-sdk.yml      # Publish SDKs to PyPI/NPM
│   └── CODEOWNERS
│
├── packages/
│   │
│   ├── api/                      # FastAPI Backend
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── main.py          # FastAPI app
│   │   │   ├── routes/
│   │   │   ├── workers/         # ARQ job processors
│   │   │   ├── brain/           # LiteLLM router
│   │   │   └── services/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── dashboard/                # Next.js Frontend
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── (auth)/
│   │   │   └── (dashboard)/
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── mobile/
│   │   │   └── visualizations/
│   │   ├── lib/
│   │   ├── public/
│   │   ├── package.json
│   │   ├── next.config.js
│   │   └── README.md
│   │
│   ├── sdk-python/               # Python SDK
│   │   ├── codewarden/
│   │   │   ├── __init__.py
│   │   │   ├── middleware/
│   │   │   ├── scrubber/
│   │   │   ├── scanner/
│   │   │   ├── evidence/
│   │   │   └── handshake/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   └── sdk-js/                   # JavaScript SDK
│       ├── src/
│       │   ├── index.ts
│       │   ├── CodeWarden.ts
│       │   ├── middleware/
│       │   ├── guards/
│       │   └── scrubber/
│       ├── tests/
│       ├── package.json
│       ├── tsconfig.json
│       └── README.md
│
├── docs/                         # Documentation site
│   ├── getting-started/
│   ├── features/
│   ├── sdk/
│   └── api/
│
├── infrastructure/               # IaC and deployment configs
│   ├── terraform/
│   ├── railway.toml
│   └── vercel.json
│
└── scripts/                      # Development utilities
    ├── setup.sh                 # First-time setup
    ├── dev.sh                   # Start local environment
    └── release.sh               # Version bump and release
```

### 9.3 Local Development Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  # ─────────────────────────────────────────────────
  # DATABASE LAYER
  # ─────────────────────────────────────────────────
  supabase-db:
    image: supabase/postgres:15.1.0.117
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: postgres
    volumes:
      - supabase-data:/var/lib/postgresql/data
  
  supabase-studio:
    image: supabase/studio:latest
    ports:
      - "3001:3000"
    environment:
      SUPABASE_URL: http://supabase-kong:8000
      STUDIO_PG_META_URL: http://supabase-meta:8080
  
  # ─────────────────────────────────────────────────
  # CACHE / QUEUE LAYER
  # ─────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
  
  # ─────────────────────────────────────────────────
  # LOG STORAGE
  # ─────────────────────────────────────────────────
  openobserve:
    image: openobserve/openobserve:latest
    ports:
      - "5080:5080"
    environment:
      ZO_ROOT_USER_EMAIL: admin@codewarden.local
      ZO_ROOT_USER_PASSWORD: admin123
      ZO_DATA_DIR: /data
    volumes:
      - openobserve-data:/data
  
  # ─────────────────────────────────────────────────
  # APPLICATION LAYER
  # ─────────────────────────────────────────────────
  api:
    build: ./packages/api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@supabase-db:5432/postgres
      REDIS_URL: redis://redis:6379
      OPENOBSERVE_URL: http://openobserve:5080
      GOOGLE_API_KEY: ${GOOGLE_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - supabase-db
      - redis
      - openobserve
    volumes:
      - ./packages/api:/app
    command: uvicorn api.main:app --reload --host 0.0.0.0
  
  dashboard:
    build: ./packages/dashboard
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NEXT_PUBLIC_SUPABASE_URL: http://localhost:8000
    volumes:
      - ./packages/dashboard:/app
      - /app/node_modules
    command: npm run dev

volumes:
  supabase-data:
  redis-data:
  openobserve-data:
```

### 9.4 Development Commands

```bash
# scripts/dev.sh

#!/bin/bash
set -e

case "$1" in
  setup)
    # First-time setup
    echo "🛠️  Setting up CodeWarden development environment..."
    cp .env.example .env
    docker-compose pull
    docker-compose up -d supabase-db redis openobserve
    sleep 5
    cd packages/api && pip install -e ".[dev]" && cd ../..
    cd packages/sdk-python && pip install -e ".[dev]" && cd ../..
    cd packages/dashboard && npm install && cd ../..
    cd packages/sdk-js && npm install && cd ../..
    echo "✅ Setup complete! Run './scripts/dev.sh start' to begin."
    ;;
    
  start)
    # Start all services
    echo "🚀 Starting CodeWarden..."
    docker-compose up -d
    echo "✅ Services running:"
    echo "   API:        http://localhost:8000"
    echo "   Dashboard:  http://localhost:3000"
    echo "   Supabase:   http://localhost:3001"
    echo "   OpenObserve: http://localhost:5080"
    ;;
    
  stop)
    docker-compose down
    ;;
    
  logs)
    docker-compose logs -f ${2:-api}
    ;;
    
  test)
    # Run all tests
    cd packages/api && pytest && cd ../..
    cd packages/sdk-python && pytest && cd ../..
    cd packages/sdk-js && npm test && cd ../..
    cd packages/dashboard && npm test && cd ../..
    ;;
    
  *)
    echo "Usage: ./scripts/dev.sh {setup|start|stop|logs|test}"
    ;;
esac
```

### 9.5 CI/CD Pipelines

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # ─────────────────────────────────────────────────
  # TEST ALL PACKAGES
  # ─────────────────────────────────────────────────
  test-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - working-directory: packages/api
        run: |
          pip install -e ".[dev]"
          pytest --cov
  
  test-sdk-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - working-directory: packages/sdk-python
        run: |
          pip install -e ".[dev]"
          pytest --cov
  
  test-sdk-js:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - working-directory: packages/sdk-js
        run: |
          npm ci
          npm test
  
  test-dashboard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - working-directory: packages/dashboard
        run: |
          npm ci
          npm run lint
          npm run build

  # ─────────────────────────────────────────────────
  # DEPLOY ON MERGE TO MAIN
  # ─────────────────────────────────────────────────
  deploy:
    needs: [test-api, test-sdk-python, test-sdk-js, test-dashboard]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Deploy API to Railway
      - name: Deploy API
        uses: railwayapp/railway-action@v1
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: api
      
      # Deploy Dashboard to Vercel
      - name: Deploy Dashboard
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
          working-directory: packages/dashboard
```

---

## 10. Data Flow Architecture

### 10.1 Error Capture Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       ERROR CAPTURE DATA FLOW                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. USER'S APP                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  @app.post("/checkout")                                          │   │
│  │  async def checkout(cart: Cart):                                 │   │
│  │      price = calculate_total(cart)  # 💥 ZeroDivisionError      │   │
│  │      ...                                                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│                                  ▼                                      │
│  2. SDK MIDDLEWARE INTERCEPTS                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  try:                                                            │   │
│  │      response = await call_next(request)                         │   │
│  │  except Exception as e:                                          │   │
│  │      self.capture_error(e)  # ◀── Caught here                   │   │
│  │      raise                                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│                                  ▼                                      │
│  3. AIRLOCK SCRUBS PII                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Raw: "User john@acme.com checkout failed with card 4111..."    │   │
│  │                              │                                   │   │
│  │                              ▼                                   │   │
│  │  Scrubbed: "User [EMAIL] checkout failed with card [CC]..."     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│                                  ▼ HTTPS POST                           │
│  4. GATEWAY RECEIVES                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  POST /v1/telemetry                                              │   │
│  │  {                                                               │   │
│  │    "type": "crash",                                              │   │
│  │    "error_type": "ZeroDivisionError",                            │   │
│  │    "trace_scrubbed": "..."                                       │   │
│  │  }                                                               │   │
│  │                                                                  │   │
│  │  Response: {"id": "evt_abc123", "status": "queued"}             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│                                  ▼ Enqueue                              │
│  5. JOB QUEUE PROCESSES                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  async def process_telemetry(event_id, payload):                 │   │
│  │      # 5a. AI Analysis                                           │   │
│  │      analysis = await ai_router.analyze(payload)                 │   │
│  │                                                                  │   │
│  │      # 5b. Store in OpenObserve                                  │   │
│  │      await openobserve.ingest(stream="errors", data={...})       │   │
│  │                                                                  │   │
│  │      # 5c. Update Supabase metadata                              │   │
│  │      await supabase.table("events").insert({...})                │   │
│  │                                                                  │   │
│  │      # 5d. Send notification                                     │   │
│  │      await notify(user, analysis)                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│                                  ▼                                      │
│  6. USER RECEIVES ALERT                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  📧 Email / 📱 Telegram                                          │   │
│  │                                                                  │   │
│  │  🚨 Critical: Checkout is broken                                 │   │
│  │                                                                  │   │
│  │  Your pricing calculation crashed because the cart was empty.    │   │
│  │                                                                  │   │
│  │  Fix: Add a check for empty carts before calculating.            │   │
│  │                                                                  │   │
│  │  [View in Dashboard →]                                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Evidence Collection Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     EVIDENCE COLLECTION FLOW                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ON APP STARTUP                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │  1. Detect version change                                        │   │
│  │     if current_version != last_version:                          │   │
│  │         evidence.log_deployment(version, commit)                 │   │
│  │                                                                  │   │
│  │  2. Run security scan                                            │   │
│  │     vulns = pip_audit.scan()                                     │   │
│  │     evidence.log_security_scan("pip-audit", status, len(vulns))  │   │
│  │                                                                  │   │
│  │  3. Check for secrets                                            │   │
│  │     secrets = secret_scanner.scan_env()                          │   │
│  │     if secrets:                                                  │   │
│  │         evidence.log_security_scan("secret-scan", "FAIL", ...)   │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│                                  ▼                                      │
│  DAILY (CRON)                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │  1. Re-run security scan (even if no changes)                    │   │
│  │  2. Log access summary                                           │   │
│  │  3. Generate uptime report                                       │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│                                  ▼                                      │
│  STORED IN SUPABASE                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  evidence_events                                                 │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │ id          │ type         │ data                       │    │   │
│  │  ├─────────────┼──────────────┼────────────────────────────┤    │   │
│  │  │ evt_001     │ AUDIT_DEPLOY │ {version: "1.0.4", ...}    │    │   │
│  │  │ evt_002     │ AUDIT_SCAN   │ {tool: "pip-audit", ...}   │    │   │
│  │  │ evt_003     │ AUDIT_ACCESS │ {user: "admin", ...}       │    │   │
│  │  └─────────────┴──────────────┴────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│                                  ▼                                      │
│  SOC 2 EXPORT (ON DEMAND)                                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │  1. Query evidence_events for date range                         │   │
│  │  2. Generate PDF reports:                                        │   │
│  │     - deployment_log.pdf                                         │   │
│  │     - security_scan_history.pdf                                  │   │
│  │     - access_audit.pdf                                           │   │
│  │     - uptime_report.pdf                                          │   │
│  │  3. Package into ZIP                                             │   │
│  │  4. Upload to R2                                                 │   │
│  │  5. Return download URL                                          │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Deployment Architecture

### 11.1 Production Infrastructure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PRODUCTION INFRASTRUCTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         CLOUDFLARE                               │   │
│  │                                                                  │   │
│  │   DNS: codewarden.io                                            │   │
│  │   DNS: api.codewarden.io                                        │   │
│  │   DNS: app.codewarden.io                                        │   │
│  │                                                                  │   │
│  │   WAF: Managed ruleset + custom rules                           │   │
│  │   DDoS: Always-on L3/L4/L7 protection                           │   │
│  │   Rate Limit: 1000 req/min/IP                                   │   │
│  │                                                                  │   │
│  └────────────────────────────┬────────────────────────────────────┘   │
│                               │                                         │
│         ┌─────────────────────┴─────────────────────┐                   │
│         │                                           │                   │
│         ▼                                           ▼                   │
│  ┌──────────────────┐                    ┌──────────────────┐          │
│  │      VERCEL      │                    │     RAILWAY      │          │
│  │                  │                    │                  │          │
│  │  app.codewarden  │                    │  api.codewarden  │          │
│  │      .io         │                    │      .io         │          │
│  │                  │                    │                  │          │
│  │  ┌────────────┐  │                    │  ┌────────────┐  │          │
│  │  │  Next.js   │  │                    │  │  FastAPI   │  │          │
│  │  │ Dashboard  │  │                    │  │  Primary   │  │          │
│  │  └────────────┘  │                    │  └────────────┘  │          │
│  │                  │                    │        │         │          │
│  │  Edge Functions  │                    │        │         │          │
│  │  Image Optim     │                    │  ┌────────────┐  │          │
│  │  Analytics       │                    │  │  FastAPI   │  │          │
│  │                  │                    │  │  Replica   │  │          │
│  └──────────────────┘                    │  └────────────┘  │          │
│                                          │                  │          │
│                                          │  Auto-scaling    │          │
│                                          │  Zero-downtime   │          │
│                                          │  deploys         │          │
│                                          └────────┬─────────┘          │
│                                                   │                     │
│         ┌─────────────────────────────────────────┼─────────┐          │
│         │                                         │         │          │
│         ▼                                         ▼         ▼          │
│  ┌──────────────┐                    ┌──────────────┐ ┌──────────┐     │
│  │   SUPABASE   │                    │   UPSTASH    │ │OPENOBSERVE│    │
│  │              │                    │              │ │          │     │
│  │  Postgres    │                    │    Redis     │ │  Logs    │     │
│  │  Auth        │                    │    Queue     │ │  Traces  │     │
│  │  Realtime    │                    │              │ │  Metrics │     │
│  │              │                    │  Serverless  │ │          │     │
│  │  Region: US  │                    │  Global      │ │  Self-   │     │
│  │  Backups: ✓  │                    │              │ │  hosted  │     │
│  └──────────────┘                    └──────────────┘ └──────────┘     │
│                                                             │          │
│                                                             │          │
│                                          ┌──────────────────┘          │
│                                          │                             │
│                                          ▼                             │
│                                   ┌──────────────┐                     │
│                                   │ CLOUDFLARE   │                     │
│                                   │     R2       │                     │
│                                   │              │                     │
│                                   │  Evidence    │                     │
│                                   │  PDFs        │                     │
│                                   │  Exports     │                     │
│                                   └──────────────┘                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Environment Configuration

```bash
# Production Environment Variables

# ─────────────────────────────────────────────────
# API (Railway)
# ─────────────────────────────────────────────────
ENVIRONMENT=production
LOG_LEVEL=info

# Database
DATABASE_URL=postgresql://user:pass@db.xxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# Redis
UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=xxx

# OpenObserve
OPENOBSERVE_URL=https://logs.codewarden.io
OPENOBSERVE_ORG=default
OPENOBSERVE_USER=admin@codewarden.io
OPENOBSERVE_PASSWORD=xxx

# AI Providers
GOOGLE_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
OPENAI_API_KEY=xxx

# Notifications
RESEND_API_KEY=re_xxx
TELEGRAM_BOT_TOKEN=xxx

# Storage
CLOUDFLARE_R2_ACCESS_KEY_ID=xxx
CLOUDFLARE_R2_SECRET_ACCESS_KEY=xxx
CLOUDFLARE_R2_BUCKET=codewarden-evidence
CLOUDFLARE_R2_ENDPOINT=https://xxx.r2.cloudflarestorage.com

# ─────────────────────────────────────────────────
# Dashboard (Vercel)
# ─────────────────────────────────────────────────
NEXT_PUBLIC_API_URL=https://api.codewarden.io
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

---

## 12. Security Architecture

### 12.1 Security Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SECURITY ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAYER 1: NETWORK SECURITY                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • Cloudflare DDoS protection (L3/L4/L7)                        │   │
│  │  • WAF with OWASP ruleset                                       │   │
│  │  • Rate limiting (API: 1000/min, SDK: 100/min)                  │   │
│  │  • TLS 1.3 everywhere                                           │   │
│  │  • HSTS enabled                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  LAYER 2: APPLICATION SECURITY                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • API key authentication (Bearer tokens)                        │   │
│  │  • Input validation (Pydantic models)                           │   │
│  │  • SQL injection prevention (parameterized queries)             │   │
│  │  • XSS prevention (React escaping, CSP headers)                 │   │
│  │  • CORS restrictions (allowed origins only)                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  LAYER 3: DATA SECURITY                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • Client-side PII scrubbing (Airlock)                          │   │
│  │  • Encryption at rest (Supabase, R2)                            │   │
│  │  • Encryption in transit (TLS 1.3)                              │   │
│  │  • API keys hashed with bcrypt                                  │   │
│  │  • Minimal data retention (configurable per plan)               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  LAYER 4: ACCESS CONTROL                                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • Role-based access (Owner, Admin, Member)                     │   │
│  │  • Organization isolation (RLS policies)                        │   │
│  │  • API key scoping (read-only vs read-write)                    │   │
│  │  • Audit logging (all admin actions)                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  LAYER 5: OPERATIONAL SECURITY                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • Secrets in environment variables (never in code)             │   │
│  │  • GitHub secret scanning enabled                               │   │
│  │  • Dependency vulnerability scanning (Dependabot)               │   │
│  │  • Regular security audits                                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.2 API Key Security

```python
# API Key Format
# cw_{environment}_{random_32_chars}
# Example: cw_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

class APIKeyManager:
    """Secure API key generation and validation."""
    
    @staticmethod
    def generate(environment: str = "live") -> tuple[str, str]:
        """Returns (raw_key, hashed_key)"""
        random_part = secrets.token_urlsafe(24)
        raw_key = f"cw_{environment}_{random_part}"
        hashed_key = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt())
        return raw_key, hashed_key.decode()
    
    @staticmethod
    def verify(raw_key: str, hashed_key: str) -> bool:
        """Constant-time comparison to prevent timing attacks."""
        return bcrypt.checkpw(raw_key.encode(), hashed_key.encode())
    
    @staticmethod
    def get_prefix(raw_key: str) -> str:
        """Extract prefix for display (e.g., 'cw_live_a1b2...')"""
        return raw_key[:16] + "..."
```

---

## 13. Scalability & Performance

### 13.1 Scaling Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SCALING STRATEGY                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  TIER 1: 0 - 1,000 Users                                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • Single Railway instance (auto-sleep okay)                    │   │
│  │  • Supabase free tier                                           │   │
│  │  • OpenObserve single node                                      │   │
│  │  • Estimated cost: $50/month                                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  TIER 2: 1,000 - 10,000 Users                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • Railway auto-scaling (2-4 instances)                         │   │
│  │  • Supabase Pro ($25/mo)                                        │   │
│  │  • OpenObserve cluster (3 nodes)                                │   │
│  │  • Upstash Redis Pro                                            │   │
│  │  • Estimated cost: $500/month                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  TIER 3: 10,000 - 100,000 Users                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • Railway dedicated instances                                  │   │
│  │  • Supabase Team ($599/mo)                                      │   │
│  │  • OpenObserve dedicated cluster                                │   │
│  │  • Read replicas for Postgres                                   │   │
│  │  • Estimated cost: $5,000/month                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  TIER 4: 100,000+ Users (Acquisition Target)                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • Kubernetes on GKE/EKS                                        │   │
│  │  • Dedicated Postgres cluster                                   │   │
│  │  • Multi-region deployment                                      │   │
│  │  • Estimated cost: $50,000+/month                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Latency (p50) | < 100ms | Time to first byte |
| API Latency (p99) | < 500ms | Time to first byte |
| Log Ingestion | < 50ms | SDK to API response |
| AI Analysis | < 5s | Queue to notification |
| Dashboard Load | < 2s | Time to interactive |
| Uptime | 99.9% | Monthly availability |

### 13.3 Bottleneck Analysis

| Component | Bottleneck Risk | Mitigation |
|-----------|-----------------|------------|
| API Server | High traffic | Railway auto-scaling |
| Redis Queue | Job backlog | Increase workers, larger instance |
| AI Analysis | Rate limits | Multi-provider, request batching |
| Postgres | Write contention | Connection pooling, read replicas |
| OpenObserve | Storage growth | Retention policies, tiered storage |

---

## 14. Disaster Recovery

### 14.1 Backup Strategy

| Component | Backup Frequency | Retention | Recovery Time |
|-----------|------------------|-----------|---------------|
| Supabase (Postgres) | Daily + PITR | 7 days (Pro), 30 days (Team) | < 1 hour |
| OpenObserve | Daily snapshots | Per plan retention | < 2 hours |
| R2 Artifacts | Cross-region replication | Indefinite | < 15 minutes |
| Redis | Upstash auto-backup | 24 hours | < 5 minutes |

### 14.2 Failover Procedures

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       FAILOVER PROCEDURES                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SCENARIO: API Server Down                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  1. Cloudflare health check fails                                │   │
│  │  2. Traffic routed to replica automatically                      │   │
│  │  3. PagerDuty alert to on-call                                   │   │
│  │  4. Railway auto-restarts failed instance                        │   │
│  │  RTO: < 1 minute                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  SCENARIO: Database Corruption                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  1. Supabase auto-detects anomaly                                │   │
│  │  2. Point-in-time restore initiated                             │   │
│  │  3. API put in maintenance mode                                  │   │
│  │  4. Restore completed, traffic resumed                          │   │
│  │  RTO: < 1 hour                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  SCENARIO: AI Provider Outage                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  1. LiteLLM detects timeout/error                                │   │
│  │  2. Automatic failover to next provider                         │   │
│  │  3. Log incident for review                                     │   │
│  │  RTO: < 5 seconds (transparent to user)                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 15. Development Environment

### 15.1 Quick Start

```bash
# Clone the repository
git clone https://github.com/codewarden/codewarden.git
cd codewarden

# First-time setup
./scripts/dev.sh setup

# Start all services
./scripts/dev.sh start

# Services available at:
# - Dashboard: http://localhost:3000
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Supabase Studio: http://localhost:3001
# - OpenObserve: http://localhost:5080
```

### 15.2 Development Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       DEVELOPMENT WORKFLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. CREATE BRANCH                                                       │
│     git checkout -b feature/my-feature                                  │
│                                                                         │
│  2. MAKE CHANGES                                                        │
│     # Edit code in packages/                                            │
│     # Hot reload active for api and dashboard                           │
│                                                                         │
│  3. TEST LOCALLY                                                        │
│     ./scripts/dev.sh test                                               │
│                                                                         │
│  4. COMMIT WITH CONVENTIONAL COMMITS                                    │
│     git commit -m "feat(api): add consensus check endpoint"            │
│                                                                         │
│  5. PUSH AND CREATE PR                                                  │
│     git push origin feature/my-feature                                  │
│     # CI runs automatically                                             │
│                                                                         │
│  6. MERGE TO MAIN                                                       │
│     # Auto-deploys to staging                                           │
│     # Manual promotion to production                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 15.3 Testing SDK Locally

```bash
# Test Python SDK against local API
cd packages/sdk-python
pip install -e ".[dev]"

# Create test FastAPI app
cat > test_app.py << 'EOF'
from fastapi import FastAPI
from codewarden import CodeWarden

app = FastAPI()
warden = CodeWarden(
    app,
    api_url="http://localhost:8000",  # Local API
    api_key="cw_test_local_dev_key"
)

@app.get("/")
def hello():
    return {"message": "Hello, CodeWarden!"}

@app.get("/crash")
def crash():
    raise ValueError("Test crash!")
EOF

# Run it
uvicorn test_app:app --reload
```

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Airlock** | Client-side PII scrubbing module |
| **ARQ** | Async Redis Queue - Python job queue |
| **Edge** | User's infrastructure where SDK runs |
| **Evidence Locker** | SOC 2 compliance artifact storage |
| **Gateway** | CodeWarden's API server |
| **LiteLLM** | AI provider abstraction library |
| **OTel** | OpenTelemetry - observability standard |
| **PII** | Personally Identifiable Information |
| **PITR** | Point-In-Time Recovery |
| **RTO** | Recovery Time Objective |
| **Vault** | Storage layer (Supabase + OpenObserve + R2) |
| **WatchDog** | Main monitoring agent in SDK |

---

## Appendix B: Decision Log

| Date | Decision | Rationale | Alternatives Considered |
|------|----------|-----------|------------------------|
| 2026-01 | Use Supabase | Managed Postgres, built-in auth | PlanetScale, Neon |
| 2026-01 | Use OpenObserve | 140x cheaper than Splunk | Loki, Elasticsearch |
| 2026-01 | Use LiteLLM | Provider-agnostic routing | Direct SDK, LangChain |
| 2026-01 | Use Railway | Simple deploys, auto-scaling | Render, Fly.io |
| 2026-01 | Monorepo | Atomic updates, unified dev | Multi-repo |
| 2026-01 | ARQ over Celery | Simpler, async-native | Celery, Dramatiq |

---

## Appendix C: References

- [OpenTelemetry Specification](https://opentelemetry.io/docs/specs/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Supabase Documentation](https://supabase.com/docs)
- [OpenObserve Documentation](https://openobserve.ai/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ARQ Documentation](https://arq-docs.helpmanual.io/)

---

**Document Control:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2026 | Engineering Team | Initial release |
