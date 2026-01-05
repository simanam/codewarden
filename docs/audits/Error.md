# CodeWarden Error Tracking Log

## Overview
This document tracks all errors encountered during development, their root causes, and solutions applied.

**Last Updated:** 2026-01-05
**Total Errors Resolved:** 5
**Active Errors:** 0

---

## Error Log Template

When encountering an error, copy this template and fill in the details:

```markdown
### ERR-XXX: [Brief Error Title]

**Date:** YYYY-MM-DD
**Status:** Active | Resolved
**Severity:** Critical | High | Medium | Low
**Phase:** Phase X.X - [Task Name]

#### Error Message
\`\`\`
[Paste exact error message here]
\`\`\`

#### Context
- **File(s) Affected:** [file paths]
- **Command/Action:** [what triggered the error]
- **Environment:** [local/staging/production]

#### Root Cause Analysis
[Explain why this error occurred]

#### Solution Applied
[Step-by-step solution that fixed the error]

#### Prevention
[How to prevent this error in the future]

#### Related Errors
- [Link to related errors if any]

---
```

---

## Error Categories

### Environment Errors (ENV)
Errors related to development environment setup, dependencies, and configuration.

### ERR-001: Poetry Installation Failed with System Python

**Date:** 2026-01-04
**Status:** Resolved
**Severity:** Medium
**Phase:** Phase 1.1 - Development Environment Setup

#### Error Message
```
Installing Poetry (2.2.1): Creating environment
Traceback (most recent call last):
  File "<stdin>", line 959, in <module>
  ...
  File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/venv/__init__.py", line 31, in should_use_symlinks
    raise Exception("This build of python cannot create venvs without using symlinks")
Exception: This build of python cannot create venvs without using symlinks
```

#### Context
- **File(s) Affected:** Poetry installation
- **Command/Action:** `curl -sSL https://install.python-poetry.org | python3 -`
- **Environment:** Local macOS

#### Root Cause Analysis
The system Python 3.9 that comes with macOS Command Line Tools has a limitation that prevents it from creating virtual environments without using symlinks. The Poetry installer was trying to use this system Python.

#### Solution Applied
1. Installed Python 3.11 via Homebrew: `brew install python@3.11`
2. Used Python 3.11 specifically for Poetry installation:
   ```bash
   curl -sSL https://install.python-poetry.org | python3.11 -
   ```
3. Added Poetry to PATH:
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

#### Prevention
- Always use Homebrew-installed Python (3.11+) for development
- Avoid using macOS system Python for anything beyond basic scripting
- Document the specific Python version requirement in setup instructions

---

---

### Build Errors (BUILD)
Errors during compilation, bundling, or build processes.

### ERR-002: Docker Compose Version Attribute Obsolete

**Date:** 2026-01-04
**Status:** Resolved
**Severity:** Low
**Phase:** Phase 1.3 - Docker Development Environment

#### Error Message
```
WARN[0000] /Users/.../codewarden/docker-compose.yml: the attribute `version` is obsolete
```

#### Context
- **File(s) Affected:** docker-compose.yml
- **Command/Action:** docker compose up
- **Environment:** Local

#### Root Cause Analysis
Docker Compose V2 no longer requires the `version` attribute at the top of compose files. It's now considered obsolete.

#### Solution Applied
Removed the `version: '3.8'` line from docker-compose.yml.

#### Prevention
Use modern Docker Compose syntax without version specification.

---

### ERR-003: Poetry README.md Not Found

**Date:** 2026-01-04
**Status:** Resolved
**Severity:** Medium
**Phase:** Phase 1.3 - Docker Development Environment

#### Error Message
```
Readme path `/app/README.md` does not exist.
```

#### Context
- **File(s) Affected:** packages/api/pyproject.toml
- **Command/Action:** docker compose build api
- **Environment:** Local Docker build

#### Root Cause Analysis
The API package's pyproject.toml referenced a README.md file that didn't exist, causing Poetry to fail during package installation in Docker.

#### Solution Applied
Created `/packages/api/README.md` with basic package documentation.

#### Prevention
Always create README.md when initializing Python packages that reference it in pyproject.toml.

---

### ERR-004: Port 3000 Already in Use

**Date:** 2026-01-04
**Status:** Resolved
**Severity:** Low
**Phase:** Phase 1.3 - Docker Development Environment

#### Error Message
```
Error response from daemon: Ports are not available: exposing port TCP 0.0.0.0:3000 -> 0.0.0.0:0: listen tcp 0.0.0.0:3000: bind: address already in use
```

#### Context
- **File(s) Affected:** docker-compose.yml (dashboard service)
- **Command/Action:** docker compose up
- **Environment:** Local

#### Root Cause Analysis
Another process was already using port 3000 on the host machine.

#### Solution Applied
Killed the process using port 3000:
```bash
lsof -ti:3000 | xargs kill -9
```

#### Prevention
Check for port conflicts before starting Docker services or use dynamic port allocation.

---

### Runtime Errors (RUNTIME)
Errors that occur during application execution.

*No errors logged yet.*

---

### Database Errors (DB)
Errors related to Supabase, migrations, or data operations.

*No errors logged yet.*

---

### API Errors (API)
Errors in the FastAPI backend or endpoint handling.

### ERR-005: FastAPI 204 Status With Response Body

**Date:** 2026-01-05
**Status:** Resolved
**Severity:** Medium
**Phase:** Phase 2.6 - API Server Core Endpoints

#### Error Message
```
AssertionError: Status code 204 must not have a response body
```

#### Context
- **File(s) Affected:** packages/api/src/api/routers/projects.py
- **Command/Action:** Starting API server
- **Environment:** Local Docker

#### Root Cause Analysis
The delete_project endpoint was defined with `status_code=status.HTTP_204_NO_CONTENT` but the function had a return type annotation that FastAPI interpreted as expecting a response body. HTTP 204 responses must not have a body.

#### Solution Applied
Changed the return type annotation from `-> None` to `-> Response`:
```python
async def delete_project(...) -> Response:
```

#### Prevention
- Always use `-> Response` return type for 204 endpoints
- Alternatively, don't specify response_model for 204 endpoints

---

### SDK Errors (SDK)
Errors in Python or JavaScript SDK development.

*No errors logged yet.*

---

### Deployment Errors (DEPLOY)
Errors during deployment to Railway, Vercel, or other platforms.

*No errors logged yet.*

---

### Integration Errors (INT)
Errors with third-party service integrations (OpenObserve, LiteLLM, etc.).

*No errors logged yet.*

---

## Common Solutions Reference

### Python Environment Issues
```bash
# Reset virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Node.js/pnpm Issues
```bash
# Clear cache and reinstall
rm -rf node_modules
pnpm store prune
pnpm install
```

### Docker Issues
```bash
# Full reset
docker-compose down -v
docker system prune -af
docker-compose up --build
```

### Supabase Connection Issues
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# Test connection
curl -X GET "$SUPABASE_URL/rest/v1/" \
  -H "apikey: $SUPABASE_ANON_KEY"
```

### Redis Connection Issues
```bash
# Test Redis connection
redis-cli ping

# Check Upstash credentials
curl -X POST "$UPSTASH_REDIS_REST_URL" \
  -H "Authorization: Bearer $UPSTASH_REDIS_REST_TOKEN" \
  -d '["PING"]'
```

---

## Error Statistics

| Category | Total | Resolved | Active |
|----------|-------|----------|--------|
| ENV | 1 | 1 | 0 |
| BUILD | 3 | 3 | 0 |
| RUNTIME | 0 | 0 | 0 |
| DB | 0 | 0 | 0 |
| API | 1 | 1 | 0 |
| SDK | 0 | 0 | 0 |
| DEPLOY | 0 | 0 | 0 |
| INT | 0 | 0 | 0 |
| **Total** | **5** | **5** | **0** |

---

## Notes

- Always log errors immediately when encountered
- Include full stack traces when available
- Document the solution even if it seems obvious
- Update the audit.md file when errors impact task progress
