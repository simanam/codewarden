# CodeWarden Development Best Practices

## Overview
This document defines coding standards, patterns, and best practices for the CodeWarden project. Follow these guidelines to ensure consistency, performance, and maintainability across all components.

**Last Updated:** 2026-01-04
**Applies To:** FastAPI Backend, Python SDK, JavaScript/TypeScript SDK, Next.js Dashboard

---

## Table of Contents
1. [FastAPI Backend Best Practices](#1-fastapi-backend-best-practices)
2. [Python SDK Best Practices](#2-python-sdk-best-practices)
3. [JavaScript/TypeScript SDK Best Practices](#3-javascripttypescript-sdk-best-practices)
4. [Next.js Dashboard Best Practices](#4-nextjs-dashboard-best-practices)
5. [General Coding Standards](#5-general-coding-standards)
6. [Security Best Practices](#6-security-best-practices)
7. [Testing Standards](#7-testing-standards)

---

## 1. FastAPI Backend Best Practices

### 1.1 Project Structure

Use the **module-functionality structure** for our monolithic application:

```
packages/api/
├── src/
│   ├── main.py                 # Application entry point
│   ├── config.py               # Pydantic Settings configuration
│   ├── dependencies.py         # Shared dependencies
│   │
│   ├── core/                   # Core utilities
│   │   ├── __init__.py
│   │   ├── security.py         # Auth helpers, JWT handling
│   │   ├── exceptions.py       # Custom exception handlers
│   │   └── middleware.py       # Custom middleware
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # Aggregates all v1 routes
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── ingest.py
│   │           ├── auth.py
│   │           ├── projects.py
│   │           └── alerts.py
│   │
│   ├── models/                 # SQLAlchemy/Database models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   └── event.py
│   │
│   ├── schemas/                # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── event.py
│   │   └── common.py
│   │
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── event_processor.py
│   │   ├── ai_analyzer.py
│   │   └── alert_service.py
│   │
│   ├── repositories/           # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── event_repository.py
│   │
│   └── workers/                # Background task workers
│       ├── __init__.py
│       └── tasks.py
│
├── tests/
│   ├── conftest.py
│   ├── test_api/
│   └── test_services/
│
├── pyproject.toml
└── Dockerfile
```

### 1.2 Async vs Sync Routes

**Rule:** Use `async def` ONLY for non-blocking I/O operations.

```python
# CORRECT - Async route with async I/O
@router.post("/events")
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event).where(Event.id == event.id))
    return result.scalars().first()

# CORRECT - Sync route for CPU-bound or sync I/O
@router.get("/health")
def health_check():
    return {"status": "healthy"}

# WRONG - Async route with blocking I/O
@router.get("/bad")
async def bad_endpoint():
    time.sleep(5)  # BLOCKS THE EVENT LOOP!
    return {"status": "done"}

# WRONG - Sync route with async client
@router.get("/also-bad")
def also_bad():
    # httpx.AsyncClient won't work here
    pass
```

### 1.3 Dependency Injection Best Practices

**Use dependencies for:**
- Database sessions
- Authentication/authorization
- Request validation
- Service instantiation

```python
# dependencies.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(
    token: Annotated[str, Depends(security)],
    db: AsyncSession = Depends(get_db)
) -> User:
    """Validate token and return current user."""
    user = await verify_token(token.credentials, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

# Using dependencies for validation
async def valid_project_id(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> Project:
    """Validate project exists and user has access."""
    project = await db.get(Project, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
```

### 1.4 Pydantic V2 Best Practices

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Annotated

# Use ConfigDict instead of class Config
class EventBase(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_min_length=1,
        from_attributes=True,  # Replaces orm_mode=True
    )

    message: str = Field(..., min_length=1, max_length=5000)
    level: Annotated[str, Field(pattern=r"^(error|warning|info|debug)$")]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Use @field_validator instead of @validator
class EventCreate(EventBase):
    project_id: str

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        if not v.startswith("proj_"):
            raise ValueError("Project ID must start with 'proj_'")
        return v

# Use declarative constraints over Python validators when possible
class UserCreate(BaseModel):
    email: Annotated[str, Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")]
    password: Annotated[str, Field(min_length=8, max_length=128)]

# Response models should be separate from create models
class EventResponse(EventBase):
    id: str
    created_at: datetime
    ai_analysis: str | None = None

# Use strict types where precision matters
from pydantic import StrictInt, StrictStr

class BillingCreate(BaseModel):
    amount_cents: StrictInt  # Won't accept "100" string
    currency: StrictStr
```

### 1.5 Error Handling

```python
# core/exceptions.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class CodeWardenException(Exception):
    """Base exception for CodeWarden."""
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code

class EventNotFound(CodeWardenException):
    def __init__(self, event_id: str):
        super().__init__(
            message=f"Event {event_id} not found",
            code="EVENT_NOT_FOUND",
            status_code=404
        )

# Register exception handler in main.py
@app.exception_handler(CodeWardenException)
async def codewarden_exception_handler(request: Request, exc: CodeWardenException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )
```

### 1.6 Configuration Management

```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App settings
    app_name: str = "CodeWarden API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    supabase_url: str
    supabase_key: str
    supabase_service_key: str

    # Redis
    redis_url: str

    # AI
    litellm_api_key: str

    # Security
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 1.7 Background Tasks

```python
# Use ARQ for reliable background jobs
from arq import create_pool
from arq.connections import RedisSettings

async def process_event(ctx: dict, event_id: str):
    """Process event with AI analysis."""
    db = ctx["db"]
    litellm = ctx["litellm"]

    event = await db.get(Event, event_id)
    if not event:
        return

    analysis = await litellm.analyze(event.stack_trace)
    event.ai_analysis = analysis
    await db.commit()

class WorkerSettings:
    functions = [process_event]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 300  # 5 minutes
```

### 1.8 API Versioning

```python
# api/v1/router.py
from fastapi import APIRouter
from .endpoints import ingest, auth, projects, alerts

router = APIRouter(prefix="/v1")
router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])

# main.py
from api.v1.router import router as v1_router

app.include_router(v1_router, prefix="/api")
```

### 1.9 Production Configuration

```python
# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = await create_redis_pool()
    app.state.db = await create_db_pool()
    yield
    # Shutdown
    await app.state.redis.close()
    await app.state.db.close()

app = FastAPI(
    title="CodeWarden API",
    lifespan=lifespan,
    # DISABLE SWAGGER IN PRODUCTION
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)
```

---

## 2. Python SDK Best Practices

### 2.1 Package Structure

```
packages/sdk-python/
├── src/
│   └── codewarden/
│       ├── __init__.py         # Public API exports
│       ├── client.py           # Main client class
│       ├── airlock.py          # PII scrubbing
│       ├── transport.py        # HTTP transport
│       ├── types.py            # Type definitions
│       ├── exceptions.py       # SDK exceptions
│       ├── _version.py         # Version info
│       │
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── flask.py
│       │   ├── django.py
│       │   └── fastapi.py
│       │
│       └── scanners/
│           ├── __init__.py
│           ├── dependencies.py
│           ├── secrets.py
│           └── static.py
│
├── tests/
├── pyproject.toml
└── README.md
```

### 2.2 pyproject.toml Configuration

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "codewarden"
version = "0.1.0"
description = "CodeWarden Python SDK - Security and observability for your applications"
readme = "README.md"
license = "MIT"
requires-python = ">=3.9"
authors = [
    { name = "CodeWarden Team", email = "team@codewarden.io" }
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Typing :: Typed",
]
dependencies = [
    "httpx>=0.25.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
flask = ["flask>=2.0.0"]
django = ["django>=4.0.0"]
fastapi = ["fastapi>=0.100.0"]
scanners = ["pip-audit>=2.6.0", "bandit>=1.7.0"]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]
all = ["codewarden[flask,django,fastapi,scanners]"]

[project.urls]
Homepage = "https://codewarden.io"
Documentation = "https://docs.codewarden.io"
Repository = "https://github.com/codewarden/codewarden-py"

[tool.hatch.build.targets.wheel]
packages = ["src/codewarden"]

[tool.ruff]
line-length = 88
target-version = "py39"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.9"
strict = true
warn_return_any = true
warn_unused_ignores = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### 2.3 Public API Design

```python
# __init__.py - Clean public API
from codewarden.client import CodeWardenClient
from codewarden.airlock import Airlock
from codewarden.exceptions import CodeWardenError, ConfigurationError
from codewarden._version import __version__

# Global client instance
_client: CodeWardenClient | None = None

def init(
    dsn: str,
    *,
    environment: str = "production",
    release: str | None = None,
    enable_pii_scrubbing: bool = True,
    debug: bool = False,
) -> CodeWardenClient:
    """
    Initialize the CodeWarden SDK.

    Args:
        dsn: Your CodeWarden DSN (from dashboard)
        environment: Environment name (e.g., "production", "staging")
        release: Optional release/version identifier
        enable_pii_scrubbing: Enable automatic PII scrubbing (default: True)
        debug: Enable debug logging (default: False)

    Returns:
        Configured CodeWardenClient instance

    Example:
        >>> import codewarden
        >>> codewarden.init("https://key@ingest.codewarden.io/123")
    """
    global _client
    _client = CodeWardenClient(
        dsn=dsn,
        environment=environment,
        release=release,
        enable_pii_scrubbing=enable_pii_scrubbing,
        debug=debug,
    )
    return _client

def get_client() -> CodeWardenClient:
    """Get the initialized client instance."""
    if _client is None:
        raise ConfigurationError(
            "CodeWarden SDK not initialized. Call codewarden.init() first."
        )
    return _client

def capture_exception(exception: BaseException) -> str:
    """Capture and send an exception to CodeWarden."""
    return get_client().capture_exception(exception)

def capture_message(message: str, level: str = "info") -> str:
    """Capture and send a message to CodeWarden."""
    return get_client().capture_message(message, level=level)

__all__ = [
    "init",
    "get_client",
    "capture_exception",
    "capture_message",
    "CodeWardenClient",
    "Airlock",
    "CodeWardenError",
    "ConfigurationError",
    "__version__",
]
```

### 2.4 Async HTTP Transport with httpx

```python
# transport.py
from __future__ import annotations

import asyncio
import httpx
from typing import Any
from collections import deque
import logging

logger = logging.getLogger(__name__)

class AsyncTransport:
    """Async HTTP transport with batching and retry logic."""

    def __init__(
        self,
        dsn: str,
        *,
        max_batch_size: int = 100,
        flush_interval: float = 5.0,
        max_retries: int = 3,
        timeout: float = 30.0,
    ):
        self._dsn = dsn
        self._max_batch_size = max_batch_size
        self._flush_interval = flush_interval
        self._max_retries = max_retries
        self._timeout = timeout

        self._queue: deque[dict[str, Any]] = deque(maxlen=10000)
        self._client: httpx.AsyncClient | None = None
        self._flush_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                ),
            )
        return self._client

    def enqueue(self, event: dict[str, Any]) -> None:
        """Add an event to the queue."""
        self._queue.append(event)

        # Start flush task if not running
        if self._flush_task is None or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._periodic_flush())

    async def _periodic_flush(self) -> None:
        """Periodically flush the queue."""
        while self._queue:
            await asyncio.sleep(self._flush_interval)
            await self.flush()

    async def flush(self) -> None:
        """Flush all queued events."""
        async with self._lock:
            if not self._queue:
                return

            # Take batch from queue
            batch = []
            while self._queue and len(batch) < self._max_batch_size:
                batch.append(self._queue.popleft())

            await self._send_batch(batch)

    async def _send_batch(self, batch: list[dict[str, Any]]) -> None:
        """Send a batch of events with retry logic."""
        client = await self._get_client()

        for attempt in range(self._max_retries):
            try:
                response = await client.post(
                    self._dsn,
                    json={"events": batch},
                )
                response.raise_for_status()
                return
            except httpx.HTTPStatusError as e:
                if e.response.status_code < 500:
                    # Client error, don't retry
                    logger.error(f"Failed to send events: {e}")
                    return
                # Server error, retry with backoff
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            except httpx.RequestError as e:
                logger.warning(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        logger.error(f"Failed to send {len(batch)} events after {self._max_retries} attempts")

    async def close(self) -> None:
        """Close the transport and flush remaining events."""
        if self._flush_task:
            self._flush_task.cancel()

        await self.flush()

        if self._client:
            await self._client.aclose()
```

### 2.5 Type Safety

```python
# types.py
from __future__ import annotations

from typing import TypedDict, Literal, Any
from datetime import datetime

class EventContext(TypedDict, total=False):
    user_id: str
    session_id: str
    request_id: str
    ip_address: str
    user_agent: str

class StackFrame(TypedDict):
    filename: str
    lineno: int
    function: str
    context_line: str | None
    pre_context: list[str]
    post_context: list[str]

class ExceptionInfo(TypedDict):
    type: str
    value: str
    module: str | None
    stacktrace: list[StackFrame]

class Event(TypedDict, total=False):
    event_id: str
    timestamp: str
    level: Literal["error", "warning", "info", "debug"]
    message: str
    exception: ExceptionInfo | None
    context: EventContext
    tags: dict[str, str]
    extra: dict[str, Any]
    environment: str
    release: str | None
```

### 2.6 Middleware Pattern

```python
# middleware/fastapi.py
from __future__ import annotations

from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import codewarden

class CodeWardenMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic error capture."""

    def __init__(
        self,
        app,
        *,
        capture_request_body: bool = False,
        ignored_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self._capture_request_body = capture_request_body
        self._ignored_paths = ignored_paths or ["/health", "/metrics"]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in self._ignored_paths:
            return await call_next(request)

        # Set request context
        client = codewarden.get_client()
        client.set_context({
            "request_id": request.headers.get("x-request-id"),
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "path": request.url.path,
            "method": request.method,
        })

        try:
            response = await call_next(request)
            return response
        except Exception as e:
            codewarden.capture_exception(e)
            raise
```

---

## 3. JavaScript/TypeScript SDK Best Practices

### 3.1 Package Structure

```
packages/sdk-js/
├── src/
│   ├── index.ts                # Public API exports
│   ├── client.ts               # Main client class
│   ├── airlock.ts              # PII scrubbing
│   ├── transport.ts            # HTTP transport
│   ├── types.ts                # Type definitions
│   │
│   ├── integrations/
│   │   ├── index.ts
│   │   ├── browser.ts          # Global error handler
│   │   └── react.tsx           # React Error Boundary
│   │
│   └── plugins/
│       ├── index.ts
│       ├── console.ts          # Console interception
│       └── network.ts          # Fetch/XHR interception
│
├── tests/
├── package.json
├── tsconfig.json
├── tsconfig.build.json
└── vite.config.ts
```

### 3.2 package.json Configuration

```json
{
  "name": "codewarden-js",
  "version": "0.1.0",
  "description": "CodeWarden JavaScript SDK",
  "type": "module",
  "main": "./dist/index.cjs",
  "module": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": {
        "types": "./dist/index.d.ts",
        "default": "./dist/index.js"
      },
      "require": {
        "types": "./dist/index.d.cts",
        "default": "./dist/index.cjs"
      }
    },
    "./react": {
      "import": {
        "types": "./dist/react.d.ts",
        "default": "./dist/react.js"
      },
      "require": {
        "types": "./dist/react.d.cts",
        "default": "./dist/react.cjs"
      }
    }
  },
  "files": [
    "dist"
  ],
  "sideEffects": false,
  "scripts": {
    "build": "tsup",
    "dev": "tsup --watch",
    "test": "vitest",
    "test:coverage": "vitest run --coverage",
    "lint": "eslint src --ext .ts,.tsx",
    "typecheck": "tsc --noEmit",
    "prepublishOnly": "pnpm run build"
  },
  "peerDependencies": {
    "react": ">=18.0.0"
  },
  "peerDependenciesMeta": {
    "react": {
      "optional": true
    }
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "eslint": "^8.0.0",
    "tsup": "^8.0.0",
    "typescript": "^5.3.0",
    "vitest": "^1.0.0"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
```

### 3.3 TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

### 3.4 Type Definitions

```typescript
// types.ts
export type LogLevel = 'error' | 'warning' | 'info' | 'debug';

export interface CodeWardenConfig {
  dsn: string;
  environment?: string;
  release?: string;
  debug?: boolean;
  enablePiiScrubbing?: boolean;
  beforeSend?: (event: Event) => Event | null;
  integrations?: Integration[];
}

export interface EventContext {
  userId?: string;
  sessionId?: string;
  requestId?: string;
  url?: string;
  userAgent?: string;
}

export interface StackFrame {
  filename: string;
  lineno: number;
  colno: number;
  function: string;
  contextLine?: string;
}

export interface ExceptionInfo {
  type: string;
  value: string;
  stacktrace: StackFrame[];
}

export interface Event {
  eventId: string;
  timestamp: string;
  level: LogLevel;
  message?: string;
  exception?: ExceptionInfo;
  context: EventContext;
  tags: Record<string, string>;
  extra: Record<string, unknown>;
  environment: string;
  release?: string;
}

export interface Integration {
  name: string;
  setup(client: CodeWardenClient): void;
  teardown?(): void;
}
```

### 3.5 Client Implementation

```typescript
// client.ts
import type { CodeWardenConfig, Event, EventContext, LogLevel } from './types';
import { Transport } from './transport';
import { Airlock } from './airlock';
import { generateEventId } from './utils';

export class CodeWardenClient {
  private readonly config: Required<CodeWardenConfig>;
  private readonly transport: Transport;
  private readonly airlock: Airlock;
  private context: EventContext = {};

  constructor(config: CodeWardenConfig) {
    this.config = {
      environment: 'production',
      release: undefined,
      debug: false,
      enablePiiScrubbing: true,
      beforeSend: (event) => event,
      integrations: [],
      ...config,
    };

    this.transport = new Transport(this.config.dsn);
    this.airlock = new Airlock();

    // Setup integrations
    for (const integration of this.config.integrations) {
      integration.setup(this);
    }
  }

  setContext(context: Partial<EventContext>): void {
    this.context = { ...this.context, ...context };
  }

  captureException(error: Error): string {
    const event = this.buildEvent('error', error.message, error);
    return this.sendEvent(event);
  }

  captureMessage(message: string, level: LogLevel = 'info'): string {
    const event = this.buildEvent(level, message);
    return this.sendEvent(event);
  }

  private buildEvent(
    level: LogLevel,
    message: string,
    error?: Error
  ): Event {
    const event: Event = {
      eventId: generateEventId(),
      timestamp: new Date().toISOString(),
      level,
      message,
      context: { ...this.context },
      tags: {},
      extra: {},
      environment: this.config.environment,
      release: this.config.release,
    };

    if (error) {
      event.exception = this.parseError(error);
    }

    // Scrub PII if enabled
    if (this.config.enablePiiScrubbing) {
      return this.airlock.scrub(event);
    }

    return event;
  }

  private sendEvent(event: Event): string {
    // Apply beforeSend hook
    const processedEvent = this.config.beforeSend(event);
    if (!processedEvent) {
      return event.eventId;
    }

    this.transport.send(processedEvent);
    return event.eventId;
  }

  private parseError(error: Error): ExceptionInfo {
    // Parse stack trace into frames
    const frames = this.parseStackTrace(error.stack);

    return {
      type: error.name,
      value: error.message,
      stacktrace: frames,
    };
  }

  private parseStackTrace(stack?: string): StackFrame[] {
    if (!stack) return [];

    // Parse stack trace format
    const lines = stack.split('\n').slice(1);
    return lines
      .map((line) => {
        const match = line.match(/at\s+(.+?)\s+\((.+):(\d+):(\d+)\)/);
        if (!match) return null;

        return {
          function: match[1],
          filename: match[2],
          lineno: parseInt(match[3], 10),
          colno: parseInt(match[4], 10),
        };
      })
      .filter((frame): frame is StackFrame => frame !== null);
  }

  async close(): Promise<void> {
    // Teardown integrations
    for (const integration of this.config.integrations) {
      integration.teardown?.();
    }

    await this.transport.flush();
  }
}
```

### 3.6 React Integration

```tsx
// integrations/react.tsx
import {
  Component,
  type ErrorInfo,
  type ReactNode,
  type ComponentType,
} from 'react';
import type { CodeWardenClient } from '../client';

interface Props {
  children: ReactNode;
  fallback?: ReactNode | ComponentType<{ error: Error; resetError: () => void }>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  error: Error | null;
}

let globalClient: CodeWardenClient | null = null;

export function setClient(client: CodeWardenClient): void {
  globalClient = client;
}

export class CodeWardenErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Capture to CodeWarden
    if (globalClient) {
      globalClient.captureException(error);
    }

    // Call custom handler
    this.props.onError?.(error, errorInfo);
  }

  resetError = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    const { error } = this.state;
    const { children, fallback } = this.props;

    if (error) {
      if (!fallback) {
        return null;
      }

      if (typeof fallback === 'function') {
        const FallbackComponent = fallback;
        return <FallbackComponent error={error} resetError={this.resetError} />;
      }

      return fallback;
    }

    return children;
  }
}
```

---

## 4. Next.js Dashboard Best Practices

### 4.1 Project Structure

```
packages/dashboard/
├── src/
│   ├── app/                        # App Router
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Dashboard home
│   │   ├── loading.tsx             # Loading UI
│   │   ├── error.tsx               # Error UI
│   │   ├── not-found.tsx           # 404 page
│   │   │
│   │   ├── (auth)/                 # Auth route group
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── signup/
│   │   │       └── page.tsx
│   │   │
│   │   ├── (dashboard)/            # Dashboard route group
│   │   │   ├── layout.tsx          # Dashboard layout with sidebar
│   │   │   ├── events/
│   │   │   │   ├── page.tsx        # Event list
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx    # Event detail
│   │   │   ├── projects/
│   │   │   │   └── page.tsx
│   │   │   └── settings/
│   │   │       └── page.tsx
│   │   │
│   │   └── api/                    # API routes (minimal)
│   │       └── auth/
│   │           └── callback/
│   │               └── route.ts
│   │
│   ├── components/
│   │   ├── ui/                     # Base UI (shadcn/ui)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   └── ...
│   │   │
│   │   ├── charts/                 # Data visualization
│   │   │   ├── error-timeline.tsx
│   │   │   ├── error-heatmap.tsx
│   │   │   └── visual-map.tsx
│   │   │
│   │   ├── layout/                 # Layout components
│   │   │   ├── sidebar.tsx
│   │   │   ├── header.tsx
│   │   │   └── navigation.tsx
│   │   │
│   │   └── features/               # Feature-specific components
│   │       ├── events/
│   │       │   ├── event-list.tsx
│   │       │   ├── event-card.tsx
│   │       │   └── event-filters.tsx
│   │       └── projects/
│   │           └── project-card.tsx
│   │
│   ├── lib/                        # Utilities
│   │   ├── supabase/
│   │   │   ├── client.ts           # Browser client
│   │   │   ├── server.ts           # Server client
│   │   │   └── middleware.ts       # Auth middleware
│   │   ├── api.ts                  # API client
│   │   └── utils.ts                # General utilities
│   │
│   ├── hooks/                      # Custom React hooks
│   │   ├── use-events.ts
│   │   ├── use-projects.ts
│   │   └── use-user.ts
│   │
│   └── types/                      # TypeScript types
│       ├── database.ts             # Supabase types
│       └── api.ts                  # API types
│
├── public/
├── next.config.ts
├── tailwind.config.ts
└── package.json
```

### 4.2 Server vs Client Components

```tsx
// RULE: Default to Server Components, use Client Components only when needed

// ✅ Server Component (default) - fetches data on server
// app/(dashboard)/events/page.tsx
import { getEvents } from '@/lib/api';
import { EventList } from '@/components/features/events/event-list';

export default async function EventsPage() {
  const events = await getEvents();

  return (
    <div>
      <h1>Events</h1>
      {/* EventList can be a Client Component for interactivity */}
      <EventList events={events} />
    </div>
  );
}

// ✅ Client Component - needs interactivity
// components/features/events/event-list.tsx
'use client';

import { useState } from 'react';
import type { Event } from '@/types/api';
import { EventCard } from './event-card';
import { EventFilters } from './event-filters';

interface EventListProps {
  events: Event[];
}

export function EventList({ events }: EventListProps) {
  const [filter, setFilter] = useState<string>('all');

  const filteredEvents = events.filter(event =>
    filter === 'all' || event.level === filter
  );

  return (
    <div>
      <EventFilters value={filter} onChange={setFilter} />
      {filteredEvents.map(event => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  );
}

// ✅ Server Component that uses Client Component
// Keeps data fetching on server, interactivity on client
```

### 4.3 Supabase Authentication

> **IMPORTANT (2025+):** Supabase has deprecated `anon` and `service_role` JWT-based keys.
> New projects should use:
> - `sb_publishable_xxx` (replaces anon key) - safe for frontend
> - `sb_secret_xxx` (replaces service_role key) - backend only
>
> See: [Supabase API Keys Documentation](https://supabase.com/docs/guides/api/api-keys)

```typescript
// lib/supabase/server.ts
import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { cookies } from 'next/headers';
import type { Database } from '@/types/database';

export async function createClient() {
  const cookieStore = await cookies();

  // Use new publishable key (2025+) or fallback to legacy anon key
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
    || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  return createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    supabaseKey!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            );
          } catch {
            // Called from Server Component
          }
        },
      },
    }
  );
}

// lib/supabase/middleware.ts
import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  // Use new publishable key (2025+) or fallback to legacy anon key
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
    || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    supabaseKey!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          );
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // Refresh session
  const { data: { user } } = await supabase.auth.getUser();

  // Protect routes
  const isAuthPage = request.nextUrl.pathname.startsWith('/login') ||
                     request.nextUrl.pathname.startsWith('/signup');

  if (!user && !isAuthPage) {
    const url = request.nextUrl.clone();
    url.pathname = '/login';
    return NextResponse.redirect(url);
  }

  if (user && isAuthPage) {
    const url = request.nextUrl.clone();
    url.pathname = '/';
    return NextResponse.redirect(url);
  }

  return supabaseResponse;
}
```

### 4.4 Data Fetching Patterns

```typescript
// lib/api.ts
import { createClient } from '@/lib/supabase/server';

export async function getEvents(options?: {
  limit?: number;
  level?: string;
  projectId?: string;
}) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    throw new Error('Unauthorized');
  }

  let query = supabase
    .from('events')
    .select('*')
    .order('created_at', { ascending: false });

  if (options?.limit) {
    query = query.limit(options.limit);
  }

  if (options?.level) {
    query = query.eq('level', options.level);
  }

  if (options?.projectId) {
    query = query.eq('project_id', options.projectId);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(error.message);
  }

  return data;
}

export async function getEvent(id: string) {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('events')
    .select('*, ai_analysis(*)')
    .eq('id', id)
    .single();

  if (error) {
    throw new Error(error.message);
  }

  return data;
}
```

### 4.5 Loading and Error States

```tsx
// app/(dashboard)/events/loading.tsx
import { Skeleton } from '@/components/ui/skeleton';

export default function Loading() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-48" />
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-24 w-full" />
      ))}
    </div>
  );
}

// app/(dashboard)/events/error.tsx
'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log to error reporting service
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px]">
      <h2 className="text-xl font-semibold mb-4">Something went wrong!</h2>
      <p className="text-muted-foreground mb-4">{error.message}</p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
```

### 4.6 Environment Variables

```typescript
// next.config.ts
import type { NextConfig } from 'next';

const config: NextConfig = {
  experimental: {
    // Enable features as needed
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '*.supabase.co',
      },
    ],
  },
};

export default config;

// lib/env.ts - Type-safe environment variables
import { z } from 'zod';

const envSchema = z.object({
  NEXT_PUBLIC_SUPABASE_URL: z.string().url(),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1),
  SUPABASE_SERVICE_ROLE_KEY: z.string().min(1),
  NEXT_PUBLIC_API_URL: z.string().url(),
});

export const env = envSchema.parse({
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  SUPABASE_SERVICE_ROLE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY,
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
});
```

---

## 5. General Coding Standards

### 5.1 Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| **Python** | | |
| Variables | snake_case | `user_name`, `event_count` |
| Functions | snake_case | `get_user()`, `process_event()` |
| Classes | PascalCase | `EventProcessor`, `CodeWardenClient` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private | Leading underscore | `_internal_method()`, `_cache` |
| **TypeScript** | | |
| Variables | camelCase | `userName`, `eventCount` |
| Functions | camelCase | `getUser()`, `processEvent()` |
| Classes | PascalCase | `EventProcessor`, `CodeWardenClient` |
| Constants | UPPER_SNAKE_CASE or camelCase | `MAX_RETRIES`, `maxRetries` |
| Types/Interfaces | PascalCase | `EventContext`, `UserProfile` |
| **Files** | | |
| Python | snake_case | `event_processor.py` |
| TypeScript | kebab-case | `event-processor.ts` |
| React Components | kebab-case | `event-card.tsx` |

### 5.2 Code Comments

```python
# Python - Use docstrings for public APIs
def process_event(event: Event, *, scrub_pii: bool = True) -> ProcessedEvent:
    """
    Process an event for ingestion.

    Args:
        event: The event to process.
        scrub_pii: Whether to scrub PII from the event. Defaults to True.

    Returns:
        The processed event ready for storage.

    Raises:
        ValidationError: If the event fails validation.

    Example:
        >>> event = Event(message="Error occurred")
        >>> processed = process_event(event)
    """
    # Implementation
```

```typescript
// TypeScript - Use JSDoc for public APIs
/**
 * Process an event for ingestion.
 *
 * @param event - The event to process
 * @param options - Processing options
 * @returns The processed event ready for storage
 * @throws {ValidationError} If the event fails validation
 *
 * @example
 * ```ts
 * const event = { message: "Error occurred" };
 * const processed = processEvent(event);
 * ```
 */
function processEvent(
  event: Event,
  options?: ProcessOptions
): ProcessedEvent {
  // Implementation
}
```

### 5.3 Import Organization

```python
# Python imports - use isort
# 1. Standard library
import asyncio
import json
from datetime import datetime
from typing import Any

# 2. Third-party
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 3. Local
from codewarden.airlock import Airlock
from codewarden.transport import Transport
```

```typescript
// TypeScript imports
// 1. External packages
import { z } from 'zod';
import { createClient } from '@supabase/supabase-js';

// 2. Internal absolute imports
import { Button } from '@/components/ui/button';
import { getEvents } from '@/lib/api';
import type { Event } from '@/types/api';

// 3. Relative imports
import { EventCard } from './event-card';
```

---

## 6. Security Best Practices

### 6.1 Input Validation

```python
# Always validate at boundaries
from pydantic import BaseModel, Field, field_validator
import re

class EventCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    level: str = Field(..., pattern=r"^(error|warning|info|debug)$")
    project_id: str

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        if not re.match(r"^proj_[a-zA-Z0-9]{20}$", v):
            raise ValueError("Invalid project ID format")
        return v
```

### 6.2 SQL Injection Prevention

```python
# Use parameterized queries - NEVER string interpolation
# ❌ WRONG
query = f"SELECT * FROM events WHERE id = '{event_id}'"

# ✅ CORRECT - Using Supabase client (handles parameterization)
result = await supabase.from_("events").select("*").eq("id", event_id).execute()

# ✅ CORRECT - Using SQLAlchemy
result = await db.execute(select(Event).where(Event.id == event_id))
```

### 6.3 Authentication Best Practices

```typescript
// Always verify user on server
import { createClient } from '@/lib/supabase/server';

export async function getProtectedData() {
  const supabase = await createClient();

  // ALWAYS call getUser() - don't trust session alone
  const { data: { user }, error } = await supabase.auth.getUser();

  if (error || !user) {
    throw new Error('Unauthorized');
  }

  // RLS will automatically scope to user
  const { data } = await supabase.from('events').select('*');
  return data;
}
```

### 6.4 Secrets Management

```python
# Never hardcode secrets
# ❌ WRONG
API_KEY = "sk-1234567890"

# ✅ CORRECT
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str  # Loaded from environment

settings = Settings()
```

### 6.5 Row Level Security (Supabase)

```sql
-- Enable RLS on all tables
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Users can only see their own projects' events
CREATE POLICY "Users can view own events" ON events
    FOR SELECT
    USING (
        project_id IN (
            SELECT id FROM projects WHERE owner_id = auth.uid()
        )
    );

-- Users can only insert to own projects
CREATE POLICY "Users can insert to own projects" ON events
    FOR INSERT
    WITH CHECK (
        project_id IN (
            SELECT id FROM projects WHERE owner_id = auth.uid()
        )
    );
```

---

## 7. Testing Standards

### 7.1 Python Testing

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from main import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_event():
    return {
        "message": "Test error",
        "level": "error",
        "project_id": "proj_test123456789012",
    }

# tests/test_api/test_ingest.py
import pytest

@pytest.mark.asyncio
async def test_create_event(client, sample_event, auth_headers):
    response = await client.post(
        "/api/v1/ingest",
        json=sample_event,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert "event_id" in data

@pytest.mark.asyncio
async def test_create_event_unauthorized(client, sample_event):
    response = await client.post("/api/v1/ingest", json=sample_event)
    assert response.status_code == 401
```

### 7.2 TypeScript Testing

```typescript
// tests/client.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CodeWardenClient } from '../src/client';

describe('CodeWardenClient', () => {
  let client: CodeWardenClient;

  beforeEach(() => {
    client = new CodeWardenClient({
      dsn: 'https://test@ingest.codewarden.io/123',
    });
  });

  it('should capture exceptions', () => {
    const error = new Error('Test error');
    const eventId = client.captureException(error);

    expect(eventId).toBeDefined();
    expect(typeof eventId).toBe('string');
  });

  it('should scrub PII from messages', () => {
    const eventId = client.captureMessage(
      'User email: test@example.com'
    );

    // Verify PII was scrubbed (implementation detail)
    expect(eventId).toBeDefined();
  });
});
```

### 7.3 React Component Testing

```typescript
// tests/components/event-card.test.tsx
import { render, screen } from '@testing-library/react';
import { EventCard } from '@/components/features/events/event-card';

describe('EventCard', () => {
  const mockEvent = {
    id: '123',
    message: 'Test error',
    level: 'error' as const,
    timestamp: '2026-01-01T00:00:00Z',
  };

  it('renders event message', () => {
    render(<EventCard event={mockEvent} />);
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('displays error level badge', () => {
    render(<EventCard event={mockEvent} />);
    expect(screen.getByText('error')).toHaveClass('bg-red-500');
  });
});
```

### 7.4 Test Coverage Requirements

| Component | Minimum Coverage |
|-----------|------------------|
| SDK Core | 90% |
| API Endpoints | 85% |
| Services/Business Logic | 85% |
| React Components | 70% |
| Utilities | 80% |

---

## References

### FastAPI
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Production Structure](https://medium.com/@devsumitg/the-perfect-structure-for-a-large-production-ready-fastapi-app-78c55271d15c)

### Python SDK
- [Python Packaging Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [pyproject.toml Specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)

### Next.js
- [Next.js Official Documentation](https://nextjs.org/docs)
- [Next.js Production Checklist](https://nextjs.org/docs/app/guides/production-checklist)
- [Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)

### TypeScript SDK
- [Building a TypeScript Library in 2025](https://dev.to/arshadyaseen/building-a-typescript-library-in-2025-2h0i)
- [TypeScript npm packages done right](https://liblab.com/blog/typescript-npm-packages-done-right)

### Pydantic
- [Pydantic V2 Performance](https://docs.pydantic.dev/latest/concepts/performance/)
- [Pydantic V2 Best Practices](https://medium.com/algomart/working-with-pydantic-v2-the-best-practices-i-wish-i-had-known-earlier-83da3aa4d17a)

### Supabase
- [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Next.js with Supabase](https://supabase.com/docs/guides/getting-started/tutorials/with-nextjs)

### Async Python
- [HTTPX Async Support](https://www.python-httpx.org/async/)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

---

**Document Control:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-04 | CodeWarden Team | Initial release |
