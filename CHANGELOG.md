# Changelog

All notable changes to CodeWarden will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-01-05

### Added

#### Phase 1: Foundation & Infrastructure
- Initial monorepo setup with pnpm workspaces
- Docker development environment (PostgreSQL, Redis, OpenObserve)
- GitHub Actions CI/CD pipelines
- Dependabot configuration for dependency updates
- External service integrations:
  - Supabase (database & auth)
  - Upstash Redis (caching & queues)
  - Cloudflare R2 (object storage)
  - AI Providers (Google, Anthropic, OpenAI)
  - Resend (email notifications)
  - Telegram (bot notifications)

#### Phase 2: Core Product Development

##### Python SDK (`packages/sdk-python`)
- **Airlock Module** - PII scrubbing engine
  - 7 default patterns (email, phone, SSN, credit card, IP, API keys)
  - Custom pattern support
  - Recursive dictionary scrubbing
  - Event-level scrubbing

- **WatchDog Module** - Error capture and context enrichment
  - Breadcrumb tracking with thread-local storage
  - System information capture (OS, Python version, machine info)
  - Enhanced stack trace parsing with source context
  - Global exception handler hooks (`sys.excepthook`)
  - Runtime information capture

- **Transport Layer** - HTTP transport with reliability
  - Background worker thread for async sending
  - Request batching (configurable batch size)
  - Retry logic with exponential backoff
  - Queue management with overflow protection

- **Framework Middleware** - Web framework integrations
  - Base middleware class with common functionality
  - FastAPI/Starlette middleware integration
  - Automatic exception capture
  - Request ID generation and header injection
  - Client IP extraction (with proxy support)
  - Slow request logging

##### API Server (`packages/api`)
- **Core Application Structure**
  - FastAPI application with lifespan management
  - Configuration via pydantic-settings
  - CORS middleware configuration
  - Structured logging

- **Event Ingestion Endpoints**
  - `POST /api/v1/events/ingest` - Batch event ingestion
  - `POST /api/v1/events/single` - Single event ingestion
  - `GET /api/v1/events/{event_id}` - Event retrieval (stub)

- **Project Management Endpoints**
  - `POST /api/v1/projects/` - Create project with API key generation
  - `GET /api/v1/projects/` - List user projects
  - `GET /api/v1/projects/{id}` - Get project details
  - `DELETE /api/v1/projects/{id}` - Delete project
  - `POST /api/v1/projects/{id}/rotate-key` - Rotate API key

- **Authentication**
  - API key authentication via `X-API-Key` header
  - Bearer token support in Authorization header

- **Services**
  - EventProcessor service for event enrichment and processing

##### JavaScript SDK (`packages/sdk-js`) - Foundation
- TypeScript SDK core structure
- Browser error capture with stack trace parsing
- React Error Boundary component
- Client-side PII scrubbing (Airlock)
- HTTP transport layer

##### Dashboard (`packages/dashboard`) - Foundation
- Next.js 15 with App Router
- Tailwind CSS configuration
- Development and production Dockerfiles

### Infrastructure
- `docker-compose.yml` for local development
- Database initialization scripts
- GitHub Actions workflows (CI, Deploy)

### Documentation
- Implementation audit tracking (`docs/audits/audit.md`)
- Error tracking log (`docs/audits/Error.md`)
- File dependency map (`docs/audits/map.md`)
- Git branching strategy (`docs/rules.md`)
- Technical and business PRDs

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | 2026-01-05 | Initial development release - Phase 1 & 2 complete |

---

## Upcoming

### Phase 3: Frontend, Integration & Launch
- [ ] Dashboard authentication with Supabase
- [ ] Dashboard core pages (events, projects, settings)
- [ ] Background workers (ARQ)
- [ ] AI analysis integration (LiteLLM)
- [ ] Alert notification system
- [ ] Production deployment (Railway, Vercel)
