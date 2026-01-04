# CodeWarden File Dependency Map

## Overview
This document defines the relationships between files, modules, and how code dependencies flow through the CodeWarden platform.

**Last Updated:** 2026-01-04
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

## Directory Structure (Planned)

```
codewarden/
├── packages/
│   ├── api/                    # FastAPI Backend
│   │   ├── src/
│   │   │   ├── main.py         # Application entry point
│   │   │   ├── config.py       # Configuration management
│   │   │   ├── routers/        # API route handlers
│   │   │   │   ├── ingest.py   # Event ingestion endpoint
│   │   │   │   ├── auth.py     # Authentication endpoints
│   │   │   │   ├── projects.py # Project CRUD
│   │   │   │   └── alerts.py   # Alert management
│   │   │   ├── services/       # Business logic
│   │   │   │   ├── event_processor.py
│   │   │   │   ├── ai_analyzer.py
│   │   │   │   └── alert_service.py
│   │   │   ├── workers/        # ARQ background workers
│   │   │   │   ├── tasks.py
│   │   │   │   └── scheduler.py
│   │   │   ├── models/         # Pydantic models
│   │   │   └── db/             # Database operations
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
│   │   │   ├── __init__.py     # SDK initialization
│   │   │   ├── client.py       # Main client class
│   │   │   ├── airlock.py      # PII scrubbing
│   │   │   ├── transport.py    # HTTP transport
│   │   │   ├── middleware/     # Framework integrations
│   │   │   │   ├── flask.py
│   │   │   │   ├── django.py
│   │   │   │   └── fastapi.py
│   │   │   └── scanners/       # Security scanners
│   │   │       ├── dependencies.py
│   │   │       ├── secrets.py
│   │   │       └── static.py
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
│   └── imports: client.py, airlock.py
│
├── client.py (CodeWardenClient)
│   ├── depends on: transport.py
│   ├── depends on: airlock.py
│   └── configures: middleware/*
│
├── airlock.py (Airlock)
│   ├── standalone module
│   └── used by: client.py, middleware/*
│
├── transport.py (AsyncTransport)
│   ├── depends on: httpx (external)
│   └── used by: client.py
│
├── middleware/
│   ├── flask.py (CodeWardenFlask)
│   │   ├── depends on: client.py
│   │   └── depends on: airlock.py
│   │
│   ├── django.py (CodeWardenDjango)
│   │   ├── depends on: client.py
│   │   └── depends on: airlock.py
│   │
│   └── fastapi.py (CodeWardenFastAPI)
│       ├── depends on: client.py
│       └── depends on: airlock.py
│
└── scanners/
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
src/
├── main.py
│   ├── imports: routers/*
│   ├── imports: config.py
│   └── starts: workers/tasks.py
│
├── config.py
│   └── used by: all modules
│
├── routers/
│   ├── ingest.py
│   │   └── calls: services/event_processor.py
│   │
│   ├── auth.py
│   │   └── calls: db/users.py
│   │
│   ├── projects.py
│   │   └── calls: db/projects.py
│   │
│   └── alerts.py
│       └── calls: services/alert_service.py
│
├── services/
│   ├── event_processor.py
│   │   ├── depends on: db/events.py
│   │   └── queues to: workers/tasks.py
│   │
│   ├── ai_analyzer.py
│   │   ├── depends on: LiteLLM (external)
│   │   └── depends on: db/events.py
│   │
│   └── alert_service.py
│       └── depends on: db/alerts.py
│
├── workers/
│   └── tasks.py
│       ├── depends on: services/*
│       └── depends on: Redis/ARQ (external)
│
└── db/
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
