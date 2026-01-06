# CodeWarden Python SDK Reference

Complete reference documentation for the CodeWarden Python SDK.

## Installation

```bash
pip install codewarden
```

With optional dependencies:

```bash
# FastAPI/Starlette support
pip install codewarden[fastapi]

# Flask support
pip install codewarden[flask]

# Django support
pip install codewarden[django]

# All frameworks
pip install codewarden[all]
```

## Initialization

### `codewarden.init()`

Initialize the CodeWarden SDK. This must be called before any other SDK methods.

```python
import codewarden

client = codewarden.init(
    dsn="https://your-api-key@api.codewarden.io/your-project-id",
    environment="production",          # Optional: environment name
    release="1.0.0",                   # Optional: release/version identifier
    enable_pii_scrubbing=True,         # Optional: enable PII scrubbing (default: True)
    debug=False,                       # Optional: enable debug logging (default: False)
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dsn` | `str` | required | Your CodeWarden DSN from the dashboard |
| `environment` | `str` | `"production"` | Environment name (production, staging, development) |
| `release` | `str \| None` | `None` | Release or version identifier |
| `enable_pii_scrubbing` | `bool` | `True` | Enable automatic PII scrubbing |
| `debug` | `bool` | `False` | Enable debug logging |

**Returns:** `CodeWardenClient` instance

## Capturing Events

### `codewarden.capture_exception()`

Capture and send an exception to CodeWarden.

```python
try:
    process_order(order_id)
except Exception as e:
    event_id = codewarden.capture_exception(e)
    print(f"Error captured with ID: {event_id}")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `exception` | `BaseException` | The exception to capture |

**Returns:** `str` - Event ID

### `codewarden.capture_message()`

Capture and send a message to CodeWarden.

```python
# Info message
codewarden.capture_message("User completed signup")

# Warning message
codewarden.capture_message("API rate limit approaching", level="warning")

# Error message
codewarden.capture_message("Payment gateway timeout", level="error")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | required | The message to send |
| `level` | `str` | `"info"` | Log level: `debug`, `info`, `warning`, `error` |

**Returns:** `str` - Event ID

## Breadcrumbs

Breadcrumbs record events that happened before an error, providing context for debugging.

### `codewarden.add_breadcrumb()`

```python
import codewarden

# Simple breadcrumb
codewarden.add_breadcrumb("ui", "User clicked submit button")

# With additional data
codewarden.add_breadcrumb(
    category="http",
    message="API request completed",
    level="info",
    data={
        "url": "/api/orders",
        "method": "POST",
        "status_code": 201,
    }
)

# Database operation
codewarden.add_breadcrumb(
    category="database",
    message="Query executed",
    data={
        "query": "SELECT * FROM users WHERE id = ?",
        "duration_ms": 45,
    }
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `category` | `str` | required | Category (ui, http, database, auth, etc.) |
| `message` | `str` | required | Human-readable message |
| `level` | `str` | `"info"` | Log level |
| `data` | `dict \| None` | `None` | Additional structured data |

**Common Categories:**

- `ui` - User interface interactions
- `http` - HTTP requests/responses
- `database` - Database queries
- `auth` - Authentication events
- `navigation` - Page/route changes
- `console` - Console logs
- `error` - Non-fatal errors

## PII Scrubbing

The Airlock module automatically scrubs sensitive data from events.

### Default Patterns

The SDK automatically detects and masks:

| Type | Pattern | Replacement |
|------|---------|-------------|
| Email | `user@example.com` | `[EMAIL]` |
| Phone (US) | `555-123-4567` | `[PHONE]` |
| Phone (Intl) | `+1-555-123-4567` | `[PHONE]` |
| SSN | `123-45-6789` | `[SSN]` |
| Credit Card | `4111-1111-1111-1111` | `[CARD]` |
| IP Address | `192.168.1.1` | `[IP]` |
| API Keys | `sk_live_abc123...` | `[REDACTED]` |

### Custom Patterns

```python
import re
from codewarden.airlock import Airlock

# Add custom patterns
airlock = Airlock(
    additional_patterns={
        "employee_id": re.compile(r"EMP-\d{6}"),
        "internal_token": re.compile(r"INT_[A-Z0-9]{32}"),
    }
)

# Scrub text manually
clean_text = airlock.scrub("Contact EMP-123456 at user@email.com")
# Result: "Contact [REDACTED] at [EMAIL]"

# Scrub a dictionary
data = {"email": "user@test.com", "nested": {"phone": "555-1234"}}
clean_data = airlock.scrub_dict(data)
# Result: {"email": "[EMAIL]", "nested": {"phone": "[PHONE]"}}
```

### Disable PII Scrubbing

```python
codewarden.init(
    dsn="...",
    enable_pii_scrubbing=False,  # Disable scrubbing
)
```

## WatchDog Module

Enhanced error capture with system context.

### System Information

```python
from codewarden.watchdog import get_watchdog

watchdog = get_watchdog()

# Get system info
system = watchdog.get_system_info()
print(system)
# {
#     "os.name": "Darwin",
#     "os.version": "23.0.0",
#     "python.version": "3.11.0",
#     "python.implementation": "CPython",
#     "machine": "arm64",
#     "processor": "arm",
#     "hostname": "my-mac"
# }
```

### Enhanced Exception Capture

```python
from codewarden.watchdog import get_watchdog

watchdog = get_watchdog()

try:
    risky_operation()
except Exception as e:
    # Get enriched exception data
    enriched = watchdog.enrich_exception(e, context={
        "user_id": "user-123",
        "request_id": "req-456",
    })

    # Includes: exception, breadcrumbs, system info, runtime info
    print(enriched["exception"]["stacktrace"])
```

### Custom Exception Handlers

```python
from codewarden.watchdog import get_watchdog

def my_handler(exception: BaseException):
    # Custom logging, alerts, etc.
    logger.error(f"Exception caught: {exception}")

watchdog = get_watchdog()
watchdog.register_exception_handler(my_handler)

# Install sys.excepthook for unhandled exceptions
watchdog.install_sys_hook()
```

## Framework Middleware

### FastAPI / Starlette

```python
from fastapi import FastAPI
from codewarden.middleware import CodeWardenMiddleware

app = FastAPI()

app.add_middleware(
    CodeWardenMiddleware,
    capture_exceptions=True,        # Capture unhandled exceptions
    capture_request_body=False,     # Include request body (caution: PII)
    capture_response_body=False,    # Include response body
    excluded_paths=["/health", "/metrics", "/favicon.ico"],
    max_body_size=10240,            # Max body size to capture (bytes)
)
```

**Features:**

- Automatic exception capture with request context
- Request ID generation and header injection
- Client IP extraction (handles proxies)
- Slow request logging (>1s)
- Request timing

**Excluded Paths:**

Use `excluded_paths` to skip tracking for health checks, metrics, and static assets:

```python
excluded_paths=[
    "/health",
    "/healthz",
    "/ready",
    "/metrics",
    "/favicon.ico",
    "/_next/",  # Next.js static files
]
```

### Flask (Coming Soon)

```python
from flask import Flask
from codewarden.middleware.flask import CodeWardenMiddleware

app = Flask(__name__)
CodeWardenMiddleware(app)
```

### Django (Coming Soon)

```python
# settings.py
MIDDLEWARE = [
    'codewarden.middleware.django.CodeWardenMiddleware',
    # ... other middleware
]

CODEWARDEN = {
    'DSN': 'https://...',
    'CAPTURE_EXCEPTIONS': True,
}
```

## Client API

### `CodeWardenClient`

```python
from codewarden import CodeWardenClient

# Direct client instantiation (advanced)
client = CodeWardenClient(
    dsn="https://...",
    environment="production",
    release="1.0.0",
)

# Set additional context
client.set_context({
    "user_id": "user-123",
    "team_id": "team-456",
})

# Capture events
client.capture_exception(exception)
client.capture_message("Event occurred")

# Close and flush pending events
client.close()
```

### Context Management

```python
import codewarden

# Set global context (added to all events)
client = codewarden.get_client()
client.set_context({
    "user_id": "user-123",
    "organization_id": "org-456",
    "subscription_tier": "premium",
})

# Context is automatically included in captured events
codewarden.capture_message("User performed action")
```

## Transport Configuration

Events are sent asynchronously with automatic retry:

- **Batch Size:** Events are batched (default: 10 events)
- **Retry:** Failed requests retry with exponential backoff
- **Background Thread:** Events are sent in a daemon thread

```python
# Events are queued and sent automatically
codewarden.capture_message("Event 1")
codewarden.capture_message("Event 2")
codewarden.capture_message("Event 3")

# Ensure all events are sent before exit
import atexit
atexit.register(codewarden.get_client().close)
```

## Error Handling

```python
from codewarden import ConfigurationError, CodeWardenError

try:
    codewarden.capture_message("test")
except ConfigurationError:
    # SDK not initialized
    print("Call codewarden.init() first!")
except CodeWardenError as e:
    # Other SDK errors
    print(f"CodeWarden error: {e}")
```

## Best Practices

### 1. Initialize Early

```python
# app.py or main.py
import codewarden

codewarden.init(dsn=os.environ["CODEWARDEN_DSN"])

# Rest of your application...
```

### 2. Use Breadcrumbs Liberally

```python
@app.post("/orders")
async def create_order(order: OrderCreate):
    codewarden.add_breadcrumb("http", f"Creating order for user {order.user_id}")

    user = await get_user(order.user_id)
    codewarden.add_breadcrumb("database", f"Fetched user {user.email}")

    result = await process_payment(order.total)
    codewarden.add_breadcrumb("payment", f"Payment {result.status}")

    return {"order_id": result.order_id}
```

### 3. Add Context

```python
@app.middleware("http")
async def add_user_context(request, call_next):
    user = get_current_user(request)
    if user:
        client = codewarden.get_client()
        client.set_context({
            "user_id": user.id,
            "user_email": user.email,  # Will be scrubbed
            "user_role": user.role,
        })
    return await call_next(request)
```

### 4. Handle Graceful Shutdown

```python
import atexit
import signal

def shutdown():
    codewarden.get_client().close()

atexit.register(shutdown)
signal.signal(signal.SIGTERM, lambda *_: shutdown())
```
