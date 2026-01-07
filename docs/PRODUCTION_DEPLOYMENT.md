# CodeWarden Production Deployment Guide

This guide provides step-by-step instructions to deploy CodeWarden to production using our recommended cloud stack.

## Production Stack Overview

| Component | Platform | Domain | Cost |
|-----------|----------|--------|------|
| Frontend Dashboard | Vercel | `app.codewarden.io` | Free (Hobby) |
| Backend API | Railway | `api.codewarden.io` | ~$5/mo |
| Database | Supabase Cloud | Managed | Free (500MB) |
| Job Queue | Upstash | Serverless Redis | Free tier |
| Logs | OpenObserve Cloud | Managed | Free tier |
| Evidence Storage | Cloudflare R2 | S3-compatible | Pay per use |

---

## Prerequisites

### 1. Required Accounts

Create accounts on the following platforms:

- [ ] **GitHub** - Repository hosting (you likely already have this)
- [ ] **Supabase** - https://supabase.com (Database + Auth)
- [ ] **Railway** - https://railway.app (Backend hosting)
- [ ] **Vercel** - https://vercel.com (Frontend hosting)
- [ ] **Upstash** - https://upstash.com (Serverless Redis)
- [ ] **Cloudflare** - https://cloudflare.com (R2 storage + DNS)

### 2. Required Tools

Install these locally:

```bash
# Supabase CLI
brew install supabase/tap/supabase

# Railway CLI
npm install -g @railway/cli

# Vercel CLI
npm install -g vercel
```

### 3. Domain Setup

If using custom domains:
- Register `codewarden.io` (or your domain)
- Add to Cloudflare for DNS management

---

## Phase 1: Database Setup (Supabase)

### Step 1.1: Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click **New Project**
3. Configure:
   - **Name**: `codewarden-prod`
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your users
4. Click **Create new project**

### Step 1.2: Get API Credentials

Navigate to **Settings → API** and note:

```
Project URL:          https://xxxx.supabase.co
API Key (anon):       eyJhbG...  (publishable key)
API Key (service_role): eyJhbG...  (secret key - KEEP SAFE!)
```

### Step 1.3: Get Database Connection String

Navigate to **Settings → Database → Connection string** (URI format):

```
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxx.supabase.co:5432/postgres
```

### Step 1.4: Run Database Migrations

From your local machine:

```bash
# Link to your project
cd packages/api
supabase link --project-ref YOUR_PROJECT_REF

# Push migrations to production
supabase db push
```

Alternatively, run migrations manually in **SQL Editor**:
1. Go to Supabase Dashboard → SQL Editor
2. Copy contents from `packages/api/supabase/migrations/` files
3. Execute in order (by filename date)

### Step 1.5: Configure Authentication

1. Go to **Authentication → Providers**
2. Enable **Email** provider (for Magic Links)
3. Go to **Authentication → URL Configuration**
4. Set:
   - Site URL: `https://app.codewarden.io`
   - Redirect URLs: `https://app.codewarden.io/auth/callback`

---

## Phase 2: Redis Setup (Upstash)

### Step 2.1: Create Redis Database

1. Go to https://console.upstash.com
2. Click **Create Database**
3. Configure:
   - **Name**: `codewarden-prod`
   - **Region**: Same as Supabase
   - **Type**: Regional
4. Click **Create**

### Step 2.2: Get Connection Details

From the database details page, copy:

```
REDIS_URL=rediss://default:xxxxx@xxxx.upstash.io:6379
```

Note: Use `rediss://` (with SSL) for production.

---

## Phase 3: Backend Deployment (Railway)

### Step 3.1: Create Railway Project

1. Go to https://railway.app/dashboard
2. Click **New Project → Deploy from GitHub repo**
3. Select your CodeWarden repository
4. Choose **monorepo** setup

### Step 3.2: Configure API Service

1. In Railway project, click **New Service → GitHub Repo**
2. Configure build settings:

```
Root Directory: packages/api
Build Command: pip install -r requirements.txt
Start Command: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Step 3.3: Add Environment Variables

In Railway service settings, add these variables:

```bash
# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# Database (from Supabase)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_PUBLISHABLE_KEY=eyJhbG...
SUPABASE_SECRET_KEY=eyJhbG...

# Redis (from Upstash)
REDIS_URL=rediss://default:xxxxx@xxxx.upstash.io:6379

# AI Providers (at least one required for AI analysis)
GOOGLE_API_KEY=your-gemini-api-key
# ANTHROPIC_API_KEY=your-claude-api-key
# OPENAI_API_KEY=your-openai-api-key

# Notifications (optional but recommended)
RESEND_API_KEY=re_xxxxx
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# Storage (for evidence exports)
CLOUDFLARE_R2_ACCESS_KEY_ID=xxxxx
CLOUDFLARE_R2_SECRET_ACCESS_KEY=xxxxx
CLOUDFLARE_R2_BUCKET=codewarden-evidence
CLOUDFLARE_R2_ENDPOINT=https://xxxx.r2.cloudflarestorage.com

# OpenObserve (for log storage)
OPENOBSERVE_URL=https://api.openobserve.ai
OPENOBSERVE_ORG=your-org
OPENOBSERVE_USER=your-email
OPENOBSERVE_PASSWORD=your-password
```

### Step 3.4: Configure Custom Domain

1. In Railway service, go to **Settings → Domains**
2. Click **Generate Domain** (for testing) or **Custom Domain**
3. For custom domain:
   - Add `api.codewarden.io`
   - Add CNAME record in Cloudflare:
     ```
     CNAME  api  your-app.up.railway.app
     ```

### Step 3.5: Deploy

Railway auto-deploys on git push. For manual deploy:

```bash
railway up
```

---

## Phase 4: Frontend Deployment (Vercel)

### Step 4.1: Create Vercel Project

1. Go to https://vercel.com/dashboard
2. Click **Add New → Project**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `packages/dashboard`

### Step 4.2: Add Environment Variables

In Vercel project settings, add:

```bash
# Supabase (public keys only!)
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=eyJhbG...

# API URL (your Railway backend)
NEXT_PUBLIC_API_URL=https://api.codewarden.io
```

### Step 4.3: Configure Custom Domain

1. Go to **Settings → Domains**
2. Add `app.codewarden.io`
3. Add DNS records in Cloudflare:
   ```
   CNAME  app  cname.vercel-dns.com
   ```

### Step 4.4: Deploy

Vercel auto-deploys on git push to `main`. For manual deploy:

```bash
cd packages/dashboard
vercel --prod
```

---

## Phase 5: Storage Setup (Cloudflare R2)

### Step 5.1: Create R2 Bucket

1. Go to Cloudflare Dashboard → R2
2. Click **Create bucket**
3. Name: `codewarden-evidence`
4. Location: Auto (or specific region)

### Step 5.2: Create API Token

1. Go to **R2 → Manage R2 API Tokens**
2. Click **Create API token**
3. Permissions: **Object Read & Write**
4. Specify bucket: `codewarden-evidence`
5. Save the credentials:
   ```
   Access Key ID: xxxxx
   Secret Access Key: xxxxx
   ```

### Step 5.3: Get Endpoint URL

Your R2 endpoint follows this pattern:
```
https://[ACCOUNT_ID].r2.cloudflarestorage.com
```

Find your Account ID in Cloudflare Dashboard → Overview (right sidebar).

---

## Phase 6: CI/CD Pipeline (GitHub Actions)

### Step 6.1: Create Workflow File

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
  SUPABASE_PROJECT_ID: ${{ secrets.SUPABASE_PROJECT_ID }}

jobs:
  # Quality Gate
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install API dependencies
        run: |
          cd packages/api
          pip install -r requirements.txt
          pip install pytest pytest-asyncio

      - name: Run API tests
        run: |
          cd packages/api
          pytest tests/ -v

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Dashboard dependencies
        run: |
          cd packages/dashboard
          npm ci

      - name: Lint Dashboard
        run: |
          cd packages/dashboard
          npm run lint

      - name: Build Dashboard
        run: |
          cd packages/dashboard
          npm run build
        env:
          NEXT_PUBLIC_SUPABASE_URL: ${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}
          NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: ${{ secrets.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY }}
          NEXT_PUBLIC_API_URL: ${{ secrets.NEXT_PUBLIC_API_URL }}

  # Database Migrations
  migrate:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: supabase/setup-cli@v1
        with:
          version: latest

      - name: Link Supabase Project
        run: |
          cd packages/api
          supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_ID }}

      - name: Push Database Migrations
        run: |
          cd packages/api
          supabase db push

  # Deploy API to Railway
  deploy-api:
    needs: migrate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy to Railway
        run: |
          cd packages/api
          railway up --service api
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  # Deploy Dashboard to Vercel
  deploy-dashboard:
    needs: migrate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Vercel CLI
        run: npm install -g vercel

      - name: Deploy to Vercel
        run: |
          cd packages/dashboard
          vercel --prod --token ${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

  # Publish SDKs (only on version tags)
  publish-sdks:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: [deploy-api, deploy-dashboard]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install build tools
        run: pip install build twine

      - name: Build Python SDK
        run: |
          cd packages/sdk-python
          python -m build

      - name: Publish to PyPI
        run: |
          cd packages/sdk-python
          twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```

### Step 6.2: Add GitHub Secrets

Go to **Repository → Settings → Secrets and variables → Actions**

Add these secrets:

| Secret Name | Description |
|-------------|-------------|
| `SUPABASE_ACCESS_TOKEN` | From Supabase account settings |
| `SUPABASE_PROJECT_ID` | Your project ref (e.g., `abcdefghij`) |
| `RAILWAY_TOKEN` | From Railway account settings |
| `VERCEL_TOKEN` | From Vercel account settings |
| `VERCEL_ORG_ID` | From Vercel project settings |
| `VERCEL_PROJECT_ID` | From Vercel project settings |
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Supabase anon key |
| `NEXT_PUBLIC_API_URL` | `https://api.codewarden.io` |
| `PYPI_TOKEN` | For SDK publishing (optional) |

---

## Phase 7: DNS Configuration

### Cloudflare DNS Records

Add these records for `codewarden.io`:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| CNAME | `app` | `cname.vercel-dns.com` | DNS only |
| CNAME | `api` | `your-app.up.railway.app` | DNS only |
| A | `@` | Redirect to `app.codewarden.io` | Proxied |

### SSL Configuration

Both Railway and Vercel provide automatic SSL certificates. Ensure:
- Cloudflare SSL mode is set to **Full (strict)**
- Custom domains are verified on both platforms

---

## Phase 8: Post-Deployment Verification

### Checklist

- [ ] **Database**: Run `SELECT NOW()` in Supabase SQL Editor
- [ ] **API Health**: Visit `https://api.codewarden.io/health`
- [ ] **Dashboard**: Visit `https://app.codewarden.io`
- [ ] **Auth Flow**: Sign up with email, verify Magic Link works
- [ ] **API Auth**: Create an app, generate API key
- [ ] **SDK Test**: Send test event using SDK

### Health Check Endpoints

```bash
# API Health
curl https://api.codewarden.io/health

# Expected response:
# {"status": "healthy", "version": "1.0.0"}
```

### Test SDK Integration

```python
import codewarden

cw = codewarden.init(
    api_key="cw_live_xxx",
    app_name="test-app",
    environment="production"
)

# Send test event
cw.capture_exception(Exception("Test error from production"))
```

---

## Troubleshooting

### Common Issues

**1. CORS Errors**
- Ensure `NEXT_PUBLIC_API_URL` matches exactly
- Check API CORS middleware includes your frontend domain

**2. Auth Redirect Issues**
- Verify Supabase redirect URLs include production domain
- Check `NEXT_PUBLIC_SUPABASE_URL` is correct

**3. Database Connection Fails**
- Verify `DATABASE_URL` format (use pooler for serverless)
- Check Supabase project is not paused

**4. Railway Deployment Fails**
- Check build logs for missing dependencies
- Verify `requirements.txt` is complete

**5. Vercel Build Fails**
- Ensure all `NEXT_PUBLIC_*` env vars are set
- Check for TypeScript errors

### Logs

- **API Logs**: Railway Dashboard → Deployments → View Logs
- **Dashboard Logs**: Vercel Dashboard → Deployments → Functions
- **Database Logs**: Supabase Dashboard → Logs

---

## Cost Estimate (Monthly)

| Service | Tier | Estimated Cost |
|---------|------|----------------|
| Vercel | Hobby | $0 |
| Railway | Starter | $5 |
| Supabase | Free | $0 |
| Upstash | Free | $0 |
| OpenObserve | Free | $0 |
| Cloudflare R2 | Pay per use | ~$1-5 |
| **Total** | | **~$6-10/mo** |

---

## Scaling Considerations

When you outgrow free tiers:

1. **Database**: Upgrade Supabase to Pro ($25/mo) for more storage
2. **API**: Add Railway workers for background processing
3. **Redis**: Upgrade Upstash for higher throughput
4. **CDN**: Enable Cloudflare proxy for global caching

---

## Security Checklist

- [ ] All secrets stored in platform environment variables (not in code)
- [ ] `SUPABASE_SECRET_KEY` never exposed to frontend
- [ ] API rate limiting enabled
- [ ] HTTPS enforced on all endpoints
- [ ] Database row-level security (RLS) policies active
- [ ] API keys hashed before storage
- [ ] Regular dependency updates scheduled

---

## Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review platform-specific docs:
   - [Vercel Docs](https://vercel.com/docs)
   - [Railway Docs](https://docs.railway.app)
   - [Supabase Docs](https://supabase.com/docs)
3. Open an issue on GitHub
