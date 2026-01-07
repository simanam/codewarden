# Security Scanning Integration Plan

## Overview

This document outlines the plan for implementing two security scanning options for CodeWarden users:

1. **Option A: GitHub Integration** - Automatic scanning via GitHub App (easiest for non-technical users)
2. **Option B: CI/CD Integration** - SDK-based scanning in user's pipeline (more control)

Users can choose either or both options from the dashboard settings.

---

## Current State (Completed)

### SDK Scanners ✅
- Location: `packages/sdk-python/src/codewarden/scanners/`
- Implemented:
  - `dependency.py` - pip-audit wrapper for vulnerable packages
  - `secret.py` - Gitleaks-pattern secret detection
  - `code.py` - Bandit SAST analysis
- Entry point: `codewarden.run_security_scan()` and `codewarden.run_and_report_scan()`

### API Security Scanner ✅
- Location: `packages/api/src/api/services/security_scanner.py`
- Server-side scanning service
- Used by dashboard "Run Scan" button

### API Endpoints ✅
- `POST /api/dashboard/apps/{app_id}/scans` - Trigger scan
- `GET /api/dashboard/apps/{app_id}/scans` - List scans
- `GET /api/dashboard/scans/{scan_id}` - Get scan details with findings

---

## Option A: GitHub Integration (Server-Side)

### User Experience

```
1. User navigates to Settings → Integrations
2. Clicks "Connect GitHub"
3. Redirected to GitHub, authorizes CodeWarden app
4. Selects which repositories to monitor
5. Done! Scans run automatically on every push
```

### Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   User's Repo   │         │     GitHub      │         │   CodeWarden    │
│   (GitHub)      │         │     Webhooks    │         │     Server      │
└────────┬────────┘         └────────┬────────┘         └────────┬────────┘
         │                           │                           │
         │  1. User pushes code      │                           │
         │ ─────────────────────────>│                           │
         │                           │                           │
         │                           │  2. Webhook: "push event" │
         │                           │ ─────────────────────────>│
         │                           │                           │
         │                           │  3. Clone repo (private   │
         │                           │     access via GitHub App)│
         │                           │ <─────────────────────────│
         │                           │                           │
         │                           │                           │  4. Run scanners
         │                           │                           │  5. Store results
         │                           │                           │  6. Delete clone
         │                           │                           │
         │  7. (Optional) Post       │                           │
         │     PR comment with       │ <─────────────────────────│
         │     findings              │                           │
```

### Components to Build

#### 1. Database Schema

```sql
-- File: packages/api/supabase/migrations/XXX_github_integration.sql

-- Store GitHub App installations
CREATE TABLE github_connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  installation_id BIGINT NOT NULL UNIQUE,
  account_login TEXT NOT NULL,
  account_type TEXT NOT NULL CHECK (account_type IN ('User', 'Organization')),
  access_token_encrypted TEXT,
  refresh_token_encrypted TEXT,
  token_expires_at TIMESTAMPTZ,
  permissions JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Track connected repositories
CREATE TABLE connected_repos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
  github_connection_id UUID NOT NULL REFERENCES github_connections(id) ON DELETE CASCADE,
  repo_full_name TEXT NOT NULL,
  repo_id BIGINT NOT NULL,
  default_branch TEXT DEFAULT 'main',
  scan_on_push BOOLEAN DEFAULT true,
  scan_on_pr BOOLEAN DEFAULT true,
  scan_schedule TEXT, -- cron expression for scheduled scans
  last_scanned_at TIMESTAMPTZ,
  last_scan_commit TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(app_id, repo_full_name)
);

-- Index for webhook lookups
CREATE INDEX idx_connected_repos_repo_id ON connected_repos(repo_id);
CREATE INDEX idx_github_connections_installation ON github_connections(installation_id);

-- RLS Policies
ALTER TABLE github_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE connected_repos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own org github connections"
  ON github_connections FOR SELECT
  USING (org_id IN (SELECT org_id FROM profiles WHERE id = auth.uid()));

CREATE POLICY "Users can view own org connected repos"
  ON connected_repos FOR SELECT
  USING (app_id IN (SELECT id FROM apps WHERE org_id IN (SELECT org_id FROM profiles WHERE id = auth.uid())));
```

#### 2. API Router - GitHub Integration

```python
# File: packages/api/src/api/routers/github.py

"""GitHub App integration endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/integrations/github", tags=["GitHub Integration"])

class ConnectRepoRequest(BaseModel):
    app_id: str
    repo_full_name: str
    scan_on_push: bool = True
    scan_on_pr: bool = True

@router.get("/install")
async def get_install_url(user: dict = Depends(get_current_user)):
    """Get GitHub App installation URL."""
    # Returns URL to install GitHub App
    pass

@router.get("/callback")
async def github_callback(code: str, installation_id: int, setup_action: str):
    """Handle GitHub App installation callback."""
    # Exchange code for access token
    # Store in github_connections
    pass

@router.get("/repos")
async def list_available_repos(user: dict = Depends(get_current_user)):
    """List repositories available for connection."""
    # Use installation token to list repos
    pass

@router.post("/connect")
async def connect_repo(request: ConnectRepoRequest, user: dict = Depends(get_current_user)):
    """Connect a repository to a CodeWarden app."""
    pass

@router.delete("/repos/{connection_id}")
async def disconnect_repo(connection_id: str, user: dict = Depends(get_current_user)):
    """Disconnect a repository."""
    pass

@router.get("/status")
async def get_connection_status(user: dict = Depends(get_current_user)):
    """Get GitHub connection status for the organization."""
    pass
```

#### 3. Webhook Handler

```python
# File: packages/api/src/api/routers/webhooks.py

"""Webhook handlers for external integrations."""

import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events."""
    # 1. Verify webhook signature
    # 2. Parse event type (push, pull_request, etc.)
    # 3. Look up connected_repos by repo_id
    # 4. Queue scan job
    pass

async def process_push_event(payload: dict):
    """Process a push event - clone and scan."""
    # 1. Get installation token
    # 2. Clone repo to temp directory
    # 3. Run security scan
    # 4. Store results in database
    # 5. Clean up temp directory
    pass

async def process_pr_event(payload: dict):
    """Process a pull request event - scan and comment."""
    # 1. Clone repo at PR head
    # 2. Run security scan
    # 3. Post comment on PR with findings
    pass
```

#### 4. GitHub Service

```python
# File: packages/api/src/api/services/github.py

"""GitHub API integration service."""

import tempfile
import subprocess
from datetime import datetime, timedelta

class GitHubService:
    """Service for interacting with GitHub API."""

    def __init__(self, app_id: str, private_key: str):
        self.app_id = app_id
        self.private_key = private_key

    async def get_installation_token(self, installation_id: int) -> str:
        """Get an installation access token."""
        # 1. Create JWT signed with private key
        # 2. Exchange for installation token
        pass

    async def clone_repo(self, repo_full_name: str, token: str, branch: str = "main") -> str:
        """Clone a repository to a temporary directory."""
        # Returns path to cloned repo
        pass

    async def list_repos(self, installation_id: int) -> list[dict]:
        """List repositories accessible to an installation."""
        pass

    async def post_pr_comment(self, repo_full_name: str, pr_number: int, comment: str, token: str):
        """Post a comment on a pull request."""
        pass

    async def create_check_run(self, repo_full_name: str, head_sha: str, findings: list, token: str):
        """Create a GitHub check run with scan results."""
        pass

async def scan_github_repo(
    repo_full_name: str,
    installation_id: int,
    branch: str = "main",
    commit_sha: str | None = None,
) -> dict:
    """Clone and scan a GitHub repository."""
    github = GitHubService(settings.GITHUB_APP_ID, settings.GITHUB_PRIVATE_KEY)

    # Get token
    token = await github.get_installation_token(installation_id)

    # Clone to temp dir
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = await github.clone_repo(repo_full_name, token, branch)

        # Run scan
        from api.services.security_scanner import scan_codebase
        result = scan_codebase(target_path=repo_path, scan_type="full")

        # Temp dir automatically cleaned up
        return result
```

#### 5. Dashboard UI Components

```typescript
// File: packages/dashboard/src/app/(dashboard)/dashboard/settings/integrations/page.tsx

// Main integrations page with GitHub connect button

// File: packages/dashboard/src/components/integrations/github-connect.tsx

// GitHub connection component:
// - "Connect GitHub" button
// - Connected repos list
// - Toggle scan settings per repo
// - Disconnect button

// File: packages/dashboard/src/lib/api/client.ts

// Add API functions:
// - getGitHubInstallUrl()
// - getGitHubRepos()
// - connectGitHubRepo(appId, repoFullName, options)
// - disconnectGitHubRepo(connectionId)
// - getGitHubConnectionStatus()
```

#### 6. Environment Variables

```bash
# GitHub App Configuration
GITHUB_APP_ID=123456
GITHUB_APP_NAME=codewarden
GITHUB_CLIENT_ID=Iv1.abc123
GITHUB_CLIENT_SECRET=secret123
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n..."
GITHUB_WEBHOOK_SECRET=webhook_secret_123
```

### GitHub App Setup (Manual Step)

1. Go to https://github.com/settings/apps/new
2. Configure:
   - App name: `CodeWarden`
   - Homepage URL: `https://codewarden.io`
   - Callback URL: `https://api.codewarden.io/api/integrations/github/callback`
   - Webhook URL: `https://api.codewarden.io/api/webhooks/github`
   - Webhook secret: Generate and save
3. Permissions:
   - Repository contents: Read
   - Pull requests: Read & Write (for comments)
   - Checks: Read & Write (for status checks)
   - Metadata: Read
4. Subscribe to events:
   - Push
   - Pull request
5. Generate private key and download

---

## Option B: CI/CD Integration (SDK-Side)

### User Experience

```
1. User navigates to Settings → CI/CD Setup
2. Copies their API key
3. Adds secret to GitHub/GitLab
4. Copies workflow YAML
5. Commits to repo
6. Done! Scans run on every push
```

### Components to Build

#### 1. Setup Guide Page

```typescript
// File: packages/dashboard/src/app/(dashboard)/dashboard/settings/cicd/page.tsx

// Page showing:
// - API key with copy button
// - Step-by-step instructions
// - Copy-paste YAML snippets for different CI systems
// - Test connection button
```

#### 2. Pre-built CI/CD Snippets

**GitHub Actions:**
```yaml
# .github/workflows/codewarden-scan.yml
name: CodeWarden Security Scan

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install CodeWarden
        run: pip install codewarden[scanners]

      - name: Run Security Scan
        env:
          CODEWARDEN_DSN: ${{ secrets.CODEWARDEN_DSN }}
        run: |
          python << 'EOF'
          import sys
          import codewarden

          # Initialize SDK
          codewarden.init(
              dsn="${CODEWARDEN_DSN}",
              environment="${{ github.ref_name }}",
              release="${{ github.sha }}"
          )

          # Run scan and report results
          result = codewarden.run_and_report_scan(".")

          # Print summary
          print(f"\n{'='*50}")
          print(f"CodeWarden Security Scan Results")
          print(f"{'='*50}")
          print(f"Total issues: {result.total_count}")
          print(f"  Critical: {result.severity_counts['critical']}")
          print(f"  High: {result.severity_counts['high']}")
          print(f"  Medium: {result.severity_counts['medium']}")
          print(f"  Low: {result.severity_counts['low']}")

          # Fail build on critical issues
          if result.severity_counts['critical'] > 0:
              print("\n❌ Critical vulnerabilities found! Failing build.")
              sys.exit(1)

          print("\n✅ No critical vulnerabilities found.")
          EOF
```

**GitLab CI:**
```yaml
# .gitlab-ci.yml
codewarden-scan:
  image: python:3.11-slim
  stage: test
  script:
    - pip install codewarden[scanners]
    - |
      python << 'EOF'
      import sys
      import codewarden

      codewarden.init(
          dsn="$CODEWARDEN_DSN",
          environment="$CI_COMMIT_REF_NAME",
          release="$CI_COMMIT_SHA"
      )

      result = codewarden.run_and_report_scan(".")

      if result.severity_counts['critical'] > 0:
          sys.exit(1)
      EOF
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

**CircleCI:**
```yaml
# .circleci/config.yml
version: 2.1

jobs:
  security-scan:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run:
          name: Install CodeWarden
          command: pip install codewarden[scanners]
      - run:
          name: Run Security Scan
          command: |
            python -c "
            import codewarden
            codewarden.init('$CODEWARDEN_DSN')
            result = codewarden.run_and_report_scan('.')
            exit(1 if result.severity_counts['critical'] > 0 else 0)
            "

workflows:
  security:
    jobs:
      - security-scan
```

**Azure DevOps:**
```yaml
# azure-pipelines.yml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - script: pip install codewarden[scanners]
    displayName: 'Install CodeWarden'

  - script: |
      python -c "
      import codewarden
      codewarden.init('$(CODEWARDEN_DSN)')
      result = codewarden.run_and_report_scan('.')
      exit(1 if result.severity_counts['critical'] > 0 else 0)
      "
    displayName: 'Run Security Scan'
```

**Bitbucket Pipelines:**
```yaml
# bitbucket-pipelines.yml
pipelines:
  default:
    - step:
        name: Security Scan
        image: python:3.11
        script:
          - pip install codewarden[scanners]
          - |
            python -c "
            import codewarden
            codewarden.init('$CODEWARDEN_DSN')
            result = codewarden.run_and_report_scan('.')
            exit(1 if result.severity_counts['critical'] > 0 else 0)
            "
```

---

## Implementation Priority

### Phase 1: CI/CD Setup Page (1-2 days)
**Priority: HIGH** - Quick win, immediately useful

Tasks:
1. Create `/dashboard/settings/cicd` page
2. Display API key with copy button
3. Add tabbed view for different CI systems
4. Copy-to-clipboard for each YAML snippet
5. Link to documentation

### Phase 2: GitHub Integration Backend (3-4 days)
**Priority: MEDIUM** - Best UX for non-technical users

Tasks:
1. Create GitHub App on github.com (manual)
2. Add database migrations for github_connections and connected_repos
3. Implement `/api/integrations/github/*` endpoints
4. Implement `/api/webhooks/github` handler
5. Create GitHubService for API calls
6. Add clone + scan + cleanup logic

### Phase 3: GitHub Integration Frontend (2-3 days)
**Priority: MEDIUM**

Tasks:
1. Create integrations settings page
2. Build GitHubConnect component
3. Build connected repos list with toggles
4. Add disconnect functionality
5. Show scan history per repo

### Phase 4: PR Comments & Checks (1-2 days)
**Priority: LOW** - Nice to have

Tasks:
1. Post scan summary as PR comment
2. Create GitHub Check Run with annotations
3. Show findings inline in PR diff

---

## Comparison Table (For Documentation)

| Feature | GitHub Integration | CI/CD Integration |
|---------|-------------------|-------------------|
| Setup difficulty | 3 clicks | Copy YAML + add secret |
| Works with private repos | ✅ | ✅ |
| Automatic on push | ✅ | ✅ (after setup) |
| PR comments | ✅ | ❌ |
| Works with GitLab/Bitbucket | Separate integration needed | ✅ Same SDK |
| Self-hosted runners | ❌ | ✅ |
| Full control over scan timing | ❌ | ✅ |
| Code stays on your infrastructure | ❌ (cloned temporarily) | ✅ |
| Requires GitHub App approval | ✅ (for orgs) | ❌ |

---

## Security Considerations

### GitHub Integration
- Access tokens encrypted at rest
- Tokens refreshed automatically
- Cloned code deleted immediately after scan
- Webhook signatures verified
- Installation permissions are minimal (read-only for code)

### CI/CD Integration
- API key stored as CI secret
- Code never leaves user's infrastructure
- Results sent over HTTPS
- API key can be rotated anytime

---

## Files to Create

### Backend (API)
```
packages/api/src/api/
├── routers/
│   ├── github.py          # NEW - GitHub OAuth & repo management
│   └── webhooks.py        # NEW - Webhook handlers
├── services/
│   └── github.py          # NEW - GitHub API service
└── models/
    └── github.py          # NEW - Pydantic models

packages/api/supabase/migrations/
└── XXX_github_integration.sql  # NEW - Database tables
```

### Frontend (Dashboard)
```
packages/dashboard/src/
├── app/(dashboard)/dashboard/settings/
│   ├── integrations/
│   │   └── page.tsx       # NEW - Integrations overview
│   └── cicd/
│       └── page.tsx       # NEW - CI/CD setup guide
├── components/
│   └── integrations/
│       ├── github-connect.tsx    # NEW
│       ├── connected-repos.tsx   # NEW
│       └── cicd-snippets.tsx     # NEW
└── lib/api/
    └── client.ts          # UPDATE - Add GitHub API functions
```

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: CI/CD Page | 1-2 days | None |
| Phase 2: GitHub Backend | 3-4 days | GitHub App created |
| Phase 3: GitHub Frontend | 2-3 days | Phase 2 |
| Phase 4: PR Comments | 1-2 days | Phase 3 |

**Total: 7-11 days**

---

## Next Steps

1. [ ] Review and approve this plan
2. [ ] Create GitHub App (manual step)
3. [ ] Start with Phase 1 (CI/CD setup page)
4. [ ] Continue to Phase 2-4 as time permits
