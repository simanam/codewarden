# CodeWarden Python SDK

Security and observability SDK for Python applications.

## Installation

```bash
pip install codewarden
```

## Quick Start

```python
import codewarden

# Initialize with your API key (get it from https://codewarden.io)
codewarden.init(
    dsn="cw_live_YOUR_API_KEY@api.codewarden.io",
    environment="production",
)

# Capture messages
codewarden.capture_message("User signed up successfully")

# Capture exceptions
try:
    risky_operation()
except Exception as e:
    codewarden.capture_exception(e)

# Add breadcrumbs for context
codewarden.add_breadcrumb("user", "Clicked checkout button")
```

## Features

- **Error Tracking**: Automatic exception capture with full stack traces
- **PII Scrubbing**: Automatically redacts sensitive data (emails, credit cards, etc.)
- **Security Scanning**: Scan your code for vulnerabilities
- **Breadcrumbs**: Add context to your error reports

## Framework Integration

### Flask

```python
from flask import Flask
import codewarden

app = Flask(__name__)
codewarden.init(dsn="cw_live_xxx@api.codewarden.io")

@app.errorhandler(Exception)
def handle_exception(e):
    codewarden.capture_exception(e)
    return "Error", 500
```

### FastAPI

```python
from fastapi import FastAPI
import codewarden

app = FastAPI()
codewarden.init(dsn="cw_live_xxx@api.codewarden.io")

@app.exception_handler(Exception)
async def handle_exception(request, exc):
    codewarden.capture_exception(exc)
    return {"error": "Internal error"}
```

### Django

```python
# settings.py
import codewarden
codewarden.init(dsn="cw_live_xxx@api.codewarden.io")

# In your middleware or views
codewarden.capture_exception(exception)
```

## Security Scanning

```python
from codewarden import run_security_scan

# Scan your project for vulnerabilities
result = run_security_scan("./src")

print(f"Found {result.total_count} issues")
for finding in result.findings:
    print(f"[{finding.severity}] {finding.title}")
```

## Configuration Options

```python
codewarden.init(
    dsn="cw_live_xxx@api.codewarden.io",
    environment="production",      # Environment name
    release="1.0.0",              # Your app version
    enable_pii_scrubbing=True,    # Auto-scrub sensitive data
    debug=False,                  # Enable debug logging
)
```

## Links

- [Dashboard](https://codewarden.io)
- [Documentation](https://codewarden.io/docs)
- [GitHub](https://github.com/simanam/codewarden)

## License

MIT License - see [LICENSE](../../LICENSE) for details.
