# CodeWarden File Dependency Map

## Overview
This document defines the relationships between files, modules, and how code dependencies flow through the CodeWarden platform.

**Last Updated:** 2026-01-05
**Architecture:** 4-Layer Hub & Spoke

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATIONS                          │
│              (Web Apps, Python Services, Node.js Apps)               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LAYER 1: EDGE (SDKs)                           │
│  ┌──────────────────────┐    ┌──────────────────────┐               │
│  │   codewarden-py      │    │   codewarden-js      │               │
│  │   (Python SDK)       │    │   (JS/TS SDK)        │               │
│  └──────────┬───────────┘    └──────────┬───────────┘               │
└─────────────┼───────────────────────────┼───────────────────────────┘
              │                           │
              └───────────┬───────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYER 2: GATEWAY (API)                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Server                             │   │
│  │  /ingest  /auth  /projects  /alerts  /dashboard              │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             │                                        │
│  ┌──────────────────────────┼───────────────────────────────────┐   │
│  │              Redis/ARQ Background Workers                     │   │
│  │  EventProcessor │ AIAnalyzer │ AlertNotifier                 │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     LAYER 3: BRAIN (AI)                             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      LiteLLM Router                           │   │
│  │     GPT-4 │ Claude │ Gemini │ Local Models                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYER 4: VAULT (Storage)                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │
│  │   Supabase     │  │  OpenObserve   │  │   Redis Cache      │    │
│  │   (Postgres)   │  │   (Logs/OTEL)  │  │   (Session/Queue)  │    │
│  └────────────────┘  └────────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure (Current)

```
codewarden/
├── packages/
│   ├── api/                    # FastAPI Backend
│   │   ├── src/api/
│   │   │   ├── __init__.py     # Package init
│   │   │   ├── main.py         # Application entry point ✅
│   │   │   ├── config.py       # Configuration management ✅
│   │   │   ├── routers/        # API route handlers
│   │   │   │   ├── __init__.py # Router exports ✅
│   │   │   │   ├── events.py   # Event ingestion endpoints ✅
│   │   │   │   └── projects.py # Project CRUD ✅
│   │   │   ├── services/       # Business logic
│   │   │   │   ├── __init__.py # Service exports ✅
│   │   │   │   └── event_processor.py ✅
│   │   │   ├── models/         # Pydantic models
│   │   │   │   ├── __init__.py # Model exports ✅
│   │   │   │   └── events.py   # Event models ✅
│   │   │   ├── workers/        # ARQ background workers (pending)
│   │   │   └── db/             # Database operations (pending)
│   │   ├── Dockerfile          # Production image ✅
│   │   ├── README.md           # Package docs ✅
│   │   └── tests/
│   │
│   ├── dashboard/              # Next.js Frontend
│   │   ├── src/
│   │   │   ├── app/            # App Router pages
│   │   │   │   ├── page.tsx    # Dashboard home
│   │   │   │   ├── events/     # Event listing/details
│   │   │   │   ├── projects/   # Project management
│   │   │   │   └── settings/   # User settings
│   │   │   ├── components/     # React components
│   │   │   │   ├── ui/         # Base UI components
│   │   │   │   ├── charts/     # Visualization components
│   │   │   │   └── layout/     # Layout components
│   │   │   ├── lib/            # Utilities
│   │   │   │   ├── supabase.ts # Supabase client
│   │   │   │   └── api.ts      # API client
│   │   │   └── hooks/          # Custom React hooks
│   │   └── tests/
│   │
│   ├── sdk-python/             # Python SDK
│   │   ├── src/codewarden/
│   │   │   ├── __init__.py     # SDK initialization ✅
│   │   │   ├── client.py       # Main client class ✅
│   │   │   ├── types.py        # Type definitions ✅
│   │   │   ├── exceptions.py   # Custom exceptions ✅
│   │   │   ├── airlock.py      # PII scrubbing ✅
│   │   │   ├── transport.py    # HTTP transport ✅
│   │   │   ├── watchdog.py     # Error capture & context ✅
│   │   │   ├── middleware/     # Framework integrations
│   │   │   │   ├── __init__.py # Middleware exports ✅
│   │   │   │   ├── base.py     # Base middleware class ✅
│   │   │   │   ├── fastapi.py  # FastAPI integration ✅
│   │   │   │   ├── flask.py    # (pending)
│   │   │   │   └── django.py   # (pending)
│   │   │   └── scanners/       # Security scanners (pending)
│   │   │       ├── dependencies.py
│   │   │       ├── secrets.py
│   │   │       └── static.py
│   │   ├── pyproject.toml      # Package config ✅
│   │   └── tests/
│   │
│   └── sdk-js/                 # JavaScript/TypeScript SDK
│       ├── src/
│       │   ├── index.ts        # SDK entry point
│       │   ├── client.ts       # Main client class
│       │   ├── airlock.ts      # PII scrubbing
│       │   ├── transport.ts    # HTTP transport
│       │   ├── integrations/   # Framework integrations
│       │   │   ├── react.tsx   # React Error Boundary
│       │   │   └── browser.ts  # Browser error capture
│       │   └── plugins/        # Optional plugins
│       │       ├── console.ts  # Console interception
│       │       └── network.ts  # Network spy
│       └── tests/
│
├── docs/                       # Documentation
│   ├── req_docs/               # Requirements
│   └── implementation/         # Implementation guides
│
├── audits/                     # Project tracking
│   ├── audit.md                # Task tracking
│   ├── Error.md                # Error log
│   └── map.md                  # This file
│
├── docker-compose.yml          # Local development services
├── pnpm-workspace.yaml         # Monorepo configuration
└── turbo.json                  # Turborepo configuration
```

---

## Module Dependencies

### Python SDK (codewarden-py)

```
codewarden/
├── __init__.py
│   ├── imports: client.py, exceptions.py, watchdog.py
│   └── exports: init(), get_client(), capture_exception(), add_breadcrumb()
│
├── client.py (CodeWardenClient) ✅
│   ├── depends on: transport.py
│   ├── depends on: airlock.py
│   ├── depends on: types.py
│   └── configures: middleware/*
│
├── types.py ✅
│   └── defines: Event, EventContext, ExceptionInfo, StackFrame
│
├── exceptions.py ✅
│   └── defines: CodeWardenError, ConfigurationError, TransportError
│
├── airlock.py (Airlock) ✅
│   ├── depends on: types.py
│   └── used by: client.py, middleware/*
│
├── transport.py (Transport) ✅
│   ├── depends on: httpx (external)
│   ├── depends on: types.py, exceptions.py
│   └── used by: client.py
│
├── watchdog.py (WatchDog) ✅
│   ├── depends on: types.py
│   ├── provides: breadcrumb tracking
│   ├── provides: system info capture
│   └── provides: exception handler hooks
│
├── middleware/
│   ├── __init__.py ✅
│   │   └── exports: BaseMiddleware, FastAPIMiddleware
│   │
│   ├── base.py (BaseMiddleware) ✅
│   │   ├── depends on: codewarden (main module)
│   │   └── provides: request tracking, exception capture
│   │
│   └── fastapi.py (CodeWardenMiddleware) ✅
│       ├── depends on: starlette (external)
│       ├── depends on: base.py
│       └── provides: FastAPI/Starlette integration
│
└── scanners/ (pending)
    ├── dependencies.py (DependencyScanner)
    │   └── depends on: pip-audit (external)
    │
    ├── secrets.py (SecretScanner)
    │   └── standalone (gitleaks patterns)
    │
    └── static.py (StaticAnalyzer)
        └── depends on: bandit (external)
```

### JavaScript SDK (codewarden-js)

```
src/
├── index.ts
│   └── exports: client.ts, airlock.ts, integrations/*
│
├── client.ts (CodeWardenClient)
│   ├── depends on: transport.ts
│   ├── depends on: airlock.ts
│   └── configures: plugins/*
│
├── airlock.ts (Airlock)
│   ├── standalone module
│   └── used by: client.ts, integrations/*
│
├── transport.ts (Transport)
│   ├── depends on: fetch API
│   └── used by: client.ts
│
├── integrations/
│   ├── react.tsx (CodeWardenErrorBoundary)
│   │   └── depends on: client.ts
│   │
│   └── browser.ts (BrowserIntegration)
│       └── depends on: client.ts
│
└── plugins/
    ├── console.ts (ConsolePlugin)
    │   └── used by: client.ts
    │
    └── network.ts (NetworkPlugin)
        └── used by: client.ts
```

### API Server

```
src/api/
├── __init__.py ✅
│   └── exports: __version__
│
├── main.py ✅
│   ├── imports: routers/events, routers/projects
│   ├── imports: config.py
│   ├── configures: CORS, logging
│   └── provides: /health, / endpoints
│
├── config.py ✅
│   ├── depends on: pydantic-settings
│   └── provides: Settings (env vars, API keys, database URLs)
│
├── routers/
│   ├── __init__.py ✅
│   │   └── exports: events_router, projects_router
│   │
│   ├── events.py ✅
│   │   ├── depends on: models/events.py
│   │   ├── depends on: services/event_processor.py
│   │   └── provides: /api/v1/events/ingest, /single, /{id}
│   │
│   └── projects.py ✅
│       ├── depends on: models (inline Pydantic models)
│       └── provides: CRUD + rotate-key endpoints
│
├── models/
│   ├── __init__.py ✅
│   │   └── exports: Event, EventBatch, EventContext, etc.
│   │
│   └── events.py ✅
│       └── defines: Event, EventBatch, EventResponse, Breadcrumb
│
├── services/
│   ├── __init__.py ✅
│   │   └── exports: EventProcessor
│   │
│   └── event_processor.py ✅
│       ├── depends on: models/events.py
│       └── provides: process_batch(), enrich_event()
│
├── workers/ (pending)
│   └── tasks.py
│       ├── depends on: services/*
│       └── depends on: Redis/ARQ (external)
│
└── db/ (pending)
    ├── connection.py
    │   └── depends on: Supabase (external)
    │
    ├── events.py
    ├── users.py
    ├── projects.py
    └── alerts.py
```

### Dashboard

```
src/
├── app/
│   ├── layout.tsx
│   │   └── uses: components/layout/*
│   │
│   ├── page.tsx (Dashboard Home)
│   │   ├── uses: components/charts/*
│   │   └── uses: hooks/useEvents.ts
│   │
│   ├── events/
│   │   ├── page.tsx (Event List)
│   │   │   └── uses: lib/api.ts
│   │   │
│   │   └── [id]/page.tsx (Event Detail)
│   │       └── uses: components/AIInsights.tsx
│   │
│   └── settings/
│       └── page.tsx
│           └── uses: lib/supabase.ts
│
├── components/
│   ├── ui/            # shadcn/ui components
│   ├── charts/
│   │   ├── Timeline.tsx
│   │   ├── Heatmap.tsx
│   │   └── VisualMap.tsx
│   └── layout/
│       ├── Sidebar.tsx
│       └── Header.tsx
│
├── lib/
│   ├── supabase.ts
│   │   └── depends on: @supabase/supabase-js
│   │
│   └── api.ts
│       └── API client for backend
│
└── hooks/
    ├── useAuth.ts
    │   └── uses: lib/supabase.ts
    │
    └── useEvents.ts
        └── uses: lib/api.ts
```

---

## Data Flow

### Event Capture Flow
```
1. Client App → SDK captures error/event
2. SDK → Airlock scrubs PII
3. SDK → Transport sends to API
4. API /ingest → EventProcessor
5. EventProcessor → Redis Queue
6. Worker → AI Analyzer (LiteLLM)
7. AI Analyzer → Stores result in Supabase
8. Dashboard → Fetches and displays
```

### Authentication Flow
```
1. User → Dashboard login page
2. Dashboard → Supabase Auth
3. Supabase → Returns JWT
4. Dashboard → Stores JWT
5. Dashboard → API requests with JWT
6. API → Validates JWT with Supabase
```

### SDK Initialization Flow
```
Python:
1. import codewarden
2. codewarden.init(dsn="...")
3. Client created with transport
4. Airlock configured
5. Middleware attached to framework

JavaScript:
1. import { CodeWarden } from 'codewarden-js'
2. CodeWarden.init({ dsn: "..." })
3. Browser/React integration attached
4. Plugins (console, network) activated
```

---

## External Dependencies

| Package | Purpose | Used By |
|---------|---------|---------|
| FastAPI | API framework | API server |
| Supabase | Database & Auth | API, Dashboard |
| Redis/ARQ | Queue & Cache | API workers |
| LiteLLM | AI model router | AI Analyzer |
| OpenObserve | Log aggregation | API server |
| Next.js 14 | Frontend framework | Dashboard |
| httpx | Async HTTP client | Python SDK |
| pip-audit | Dependency scanning | Python SDK |
| bandit | Static analysis | Python SDK |

---

## Notes

- Update this map when adding new files or modules
- Keep dependency arrows accurate for debugging
- Use this for understanding impact of changes
