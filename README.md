# CodeWarden

> You ship the code. We stand guard.

CodeWarden is a drop-in security and observability platform designed for solopreneurs and indie developers. Monitor errors, scrub PII, and get AI-powered insights - all without the enterprise complexity.

## Features

- **Error Tracking** - Capture and analyze exceptions with full context
- **PII Scrubbing** - Automatic detection and masking of sensitive data (emails, phone numbers, SSN, credit cards, API keys)
- **AI Insights** - Get intelligent fix suggestions powered by LLMs
- **Multi-Framework Support** - SDKs for Python (FastAPI, Flask, Django) and JavaScript/TypeScript (React, Node.js)
- **Real-time Dashboard** - Monitor your applications in real-time

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop
- pnpm (`npm install -g pnpm`)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/simanam/codewarden.git
cd codewarden

# Install dependencies
pnpm install

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker compose up -d

# API available at http://localhost:8000
# Dashboard available at http://localhost:3000
```

## Architecture

CodeWarden uses a 4-layer architecture:

```
┌─────────────────────────────────────────────────┐
│  Layer 1: EDGE (SDKs)                           │
│  Python SDK | JavaScript SDK                    │
└─────────────────────┬───────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────┐
│  Layer 2: GATEWAY (API)                         │
│  FastAPI Server | Background Workers            │
└─────────────────────┬───────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────┐
│  Layer 3: BRAIN (AI)                            │
│  LiteLLM Router (GPT-4, Claude, Gemini)         │
└─────────────────────┬───────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────┐
│  Layer 4: VAULT (Storage)                       │
│  Supabase | OpenObserve | Redis                 │
└─────────────────────────────────────────────────┘
```

## Project Structure

```
packages/
├── api/          # FastAPI backend
├── dashboard/    # Next.js frontend
├── sdk-python/   # Python SDK (codewarden)
└── sdk-js/       # JavaScript SDK (codewarden-js)
```

## Python SDK Usage

```python
import codewarden

# Initialize the SDK
codewarden.init(
    dsn="https://your-key@ingest.codewarden.io/project-id",
    environment="production"
)

# Capture exceptions
try:
    risky_operation()
except Exception as e:
    codewarden.capture_exception(e)

# Add breadcrumbs for context
codewarden.add_breadcrumb("user", "User clicked submit button")

# FastAPI middleware integration
from fastapi import FastAPI
from codewarden.middleware import FastAPIMiddleware

app = FastAPI()
app.add_middleware(FastAPIMiddleware)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/events/ingest` | POST | Batch event ingestion |
| `/api/v1/events/single` | POST | Single event ingestion |
| `/api/v1/projects/` | POST | Create project |
| `/api/v1/projects/` | GET | List projects |
| `/api/v1/projects/{id}` | GET | Get project |
| `/api/v1/projects/{id}` | DELETE | Delete project |

## Development

### Running Tests

```bash
# Python tests
cd packages/sdk-python
poetry run pytest

# API tests
cd packages/api
poetry run pytest
```

### Code Quality

```bash
# Python linting
poetry run ruff check .

# Type checking
poetry run mypy .
```

## Documentation

- [Implementation Audit](docs/audits/audit.md) - Task tracking and progress
- [File Map](docs/audits/map.md) - Architecture and dependencies
- [Error Log](docs/audits/Error.md) - Encountered errors and solutions

## Technology Stack

- **Backend**: FastAPI, Python 3.11+, Poetry
- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS
- **Database**: Supabase (PostgreSQL)
- **Cache/Queue**: Redis, Upstash
- **Logging**: OpenObserve
- **AI**: LiteLLM (multi-provider)
- **Storage**: Cloudflare R2

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
