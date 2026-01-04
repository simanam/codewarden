# CodeWarden Error Tracking Log

## Overview
This document tracks all errors encountered during development, their root causes, and solutions applied.

**Last Updated:** 2026-01-04
**Total Errors Resolved:** 1
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

*No errors logged yet.*

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

*No errors logged yet.*

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
| BUILD | 0 | 0 | 0 |
| RUNTIME | 0 | 0 | 0 |
| DB | 0 | 0 | 0 |
| API | 0 | 0 | 0 |
| SDK | 0 | 0 | 0 |
| DEPLOY | 0 | 0 | 0 |
| INT | 0 | 0 | 0 |
| **Total** | **1** | **1** | **0** |

---

## Notes

- Always log errors immediately when encountered
- Include full stack traces when available
- Document the solution even if it seems obvious
- Update the audit.md file when errors impact task progress
