# CodeWarden Railway Deployment Guide

Complete guide to deploying CodeWarden on Railway.

## Prerequisites

Before starting, you need:
1. A [Railway](https://railway.app) account
2. A [Supabase](https://supabase.com) project (already set up)
3. Your GitHub repository connected to Railway

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Railway                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   API       │  │  Dashboard  │  │  OpenObserve        │  │
│  │  (FastAPI)  │  │  (Next.js)  │  │  (Log Storage)      │  │
│  │  Port: auto │  │  Port: auto │  │  Port: 5080         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │    Supabase     │
                    │  (Database +    │
                    │   Auth)         │
                    └─────────────────┘
```

---

## Step 1: Create Railway Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `codewarden` repository
5. Railway will detect the monorepo structure

---

## Step 2: Deploy the API Service

### 2.1 Create API Service

1. In your Railway project, click **"New"** → **"GitHub Repo"**
2. Select your repository
3. Click **"Add Service"**
4. In the service settings:
   - **Root Directory**: `packages/api`
   - **Builder**: Dockerfile
   - **Start Command**: (leave empty, Dockerfile handles it)

### 2.2 Configure API Environment Variables

Go to your API service → **Variables** tab → Click **"New Variable"** for each:

#### Required Variables (API won't work without these)

| Variable | Value | Where to Get |
|----------|-------|--------------|
| `SUPABASE_URL` | `https://xxxxx.supabase.co` | Supabase Dashboard → Settings → API → Project URL |
| `SUPABASE_SECRET_KEY` | `eyJhbGci...` | Supabase Dashboard → Settings → API → `service_role` secret |
| `ENVIRONMENT` | `production` | Set this exact value |
| `DEBUG` | `false` | Set this exact value |

#### Optional Variables (features disabled if not set)

| Variable | Value | Purpose |
|----------|-------|---------|
| `OPENOBSERVE_URL` | `https://your-openobserve.up.railway.app` | Log storage (see Step 4) |
| `OPENOBSERVE_ORG` | `default` | OpenObserve organization |
| `OPENOBSERVE_USER` | `admin@codewarden.io` | OpenObserve admin email |
| `OPENOBSERVE_PASSWORD` | `your-secure-password` | OpenObserve admin password |
| `GOOGLE_API_KEY` | `AIza...` | AI analysis (Gemini) |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | AI analysis (Claude) |
| `OPENAI_API_KEY` | `sk-...` | AI analysis (GPT) |
| `RESEND_API_KEY` | `re_...` | Email notifications |
| `TELEGRAM_BOT_TOKEN` | `123456:ABC...` | Telegram alerts |
| `REDIS_URL` | `redis://...` | Background job queue |

### 2.3 Generate API Domain

1. Go to API service → **Settings** → **Networking**
2. Click **"Generate Domain"**
3. You'll get something like: `api-production-xxxx.up.railway.app`
4. Note this URL - you'll need it for the Dashboard

---

## Step 3: Deploy the Dashboard Service

### 3.1 Create Dashboard Service

1. Click **"New"** → **"GitHub Repo"**
2. Select your repository again
3. In service settings:
   - **Root Directory**: `packages/dashboard`
   - **Builder**: Nixpacks (auto-detected for Next.js)

### 3.2 Configure Dashboard Environment Variables

Go to Dashboard service → **Variables** tab:

| Variable | Value | Where to Get |
|----------|-------|--------------|
| `NEXT_PUBLIC_API_URL` | `https://api-production-xxxx.up.railway.app` | From Step 2.3 |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxxx.supabase.co` | Same as API |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGci...` | Supabase → Settings → API → `anon` public key |

### 3.3 Generate Dashboard Domain

1. Go to Dashboard service → **Settings** → **Networking**
2. Click **"Generate Domain"** or add custom domain
3. For custom domain (e.g., `codewarden.io`):
   - Click **"Custom Domain"**
   - Enter your domain
   - Add the CNAME record to your DNS

---

## Step 4: Deploy OpenObserve (Optional - Log Storage)

OpenObserve stores detailed logs and stack traces. Skip this step if you don't need detailed log storage yet.

### 4.1 Create OpenObserve Service

1. Click **"New"** → **"Docker Image"**
2. Enter image: `openobserve/openobserve:latest`
3. Click **"Deploy"**

### 4.2 Configure OpenObserve Variables

| Variable | Value |
|----------|-------|
| `ZO_ROOT_USER_EMAIL` | `admin@codewarden.io` |
| `ZO_ROOT_USER_PASSWORD` | `your-secure-password-here` |
| `ZO_DATA_DIR` | `/data` |

### 4.3 Add Persistent Storage

1. Go to OpenObserve service → **Settings** → **Volumes**
2. Click **"Add Volume"**
3. Mount path: `/data`
4. This ensures logs persist across deployments

### 4.4 Generate OpenObserve Domain

1. Go to **Settings** → **Networking**
2. Click **"Generate Domain"**
3. Note the URL (e.g., `openobserve-production-xxxx.up.railway.app`)

### 4.5 Update API with OpenObserve URL

Go back to your API service → **Variables** and add:

| Variable | Value |
|----------|-------|
| `OPENOBSERVE_URL` | `https://openobserve-production-xxxx.up.railway.app` |
| `OPENOBSERVE_ORG` | `default` |
| `OPENOBSERVE_USER` | `admin@codewarden.io` |
| `OPENOBSERVE_PASSWORD` | `your-secure-password-here` |

---

## Step 5: Deploy Redis (Optional - Background Jobs)

Redis is needed for background job processing (AI analysis, notifications).

### 5.1 Add Redis

1. Click **"New"** → **"Database"** → **"Redis"**
2. Railway provisions Redis automatically
3. Railway auto-injects `REDIS_URL` to services that need it

### 5.2 Link Redis to API

1. Go to your API service
2. Click **"Variables"** → **"Add Reference"**
3. Select your Redis service
4. Choose `REDIS_URL`

---

## Step 6: Configure Supabase Auth Redirect URLs

After deployment, update Supabase to allow redirects from your Railway domains:

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project → **Authentication** → **URL Configuration**
3. Add to **Redirect URLs**:
   ```
   https://your-dashboard.up.railway.app/**
   https://codewarden.io/**
   https://www.codewarden.io/**
   ```

---

## Step 7: Update CORS in API (if needed)

If you're using a custom domain, update the CORS settings in `packages/api/src/api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://codewarden.io",
        "https://www.codewarden.io",
        "https://app.codewarden.io",
        "https://your-dashboard.up.railway.app",  # Add your Railway domain
    ],
    ...
)
```

---

## Step 8: Verify Deployment

### Test API Health

```bash
curl https://your-api.up.railway.app/health
# Should return: {"status": "healthy", "version": "0.1.0"}
```

### Test Dashboard

1. Open `https://your-dashboard.up.railway.app`
2. Try signing up with email/password or OAuth
3. Check that dashboard loads without 503 errors

### Test OpenObserve (if deployed)

1. Open `https://your-openobserve.up.railway.app`
2. Login with your admin credentials
3. Check the "Logs" section

---

## Environment Variables Quick Reference

### API Service (Required)

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SECRET_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
ENVIRONMENT=production
DEBUG=false
```

### API Service (Optional)

```env
# OpenObserve (Log Storage)
OPENOBSERVE_URL=https://openobserve-production-xxxx.up.railway.app
OPENOBSERVE_ORG=default
OPENOBSERVE_USER=admin@codewarden.io
OPENOBSERVE_PASSWORD=your-secure-password

# AI Providers (pick one or more)
GOOGLE_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Notifications
RESEND_API_KEY=re_...
TELEGRAM_BOT_TOKEN=123456:ABC...

# Redis (auto-injected if you add Railway Redis)
REDIS_URL=redis://default:xxx@xxx.railway.internal:6379
```

### Dashboard Service

```env
NEXT_PUBLIC_API_URL=https://api-production-xxxx.up.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### OpenObserve Service

```env
ZO_ROOT_USER_EMAIL=admin@codewarden.io
ZO_ROOT_USER_PASSWORD=your-secure-password
ZO_DATA_DIR=/data
```

---

## Troubleshooting

### API returns 503 "Database not available"

- Check `SUPABASE_URL` and `SUPABASE_SECRET_KEY` are set correctly
- Verify the service_role key (not the anon key) is used

### Dashboard shows "Not authenticated"

- Check `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Verify redirect URLs are configured in Supabase

### Signup fails with "Database error saving new user"

- Run the migration: `packages/api/supabase/migrations/20260106_fix_user_signup_trigger.sql`
- Or trigger CI/CD by pushing to main branch

### OpenObserve not receiving logs

- Check `OPENOBSERVE_URL` is accessible from API
- Verify credentials match between API and OpenObserve

### CORS errors in browser

- Add your domain to the CORS allow_origins list in `main.py`
- Redeploy the API

---

## Cost Estimate (Railway)

| Service | Estimated Cost |
|---------|----------------|
| API | ~$5-10/month |
| Dashboard | ~$5-10/month |
| OpenObserve | ~$5-10/month |
| Redis | ~$5/month |
| **Total** | **~$20-35/month** |

Railway offers a free tier with $5 credit/month for testing.

---

## Next Steps

After deployment:

1. Test signup flow at your dashboard URL
2. Create a test project
3. Install the Python SDK in a test app:
   ```bash
   pip install codewarden
   ```
4. Send a test error:
   ```python
   from codewarden import CodeWarden
   cw = CodeWarden(api_key="cw_live_xxx")
   cw.capture_exception(Exception("Test error"))
   ```
5. Verify it appears in your dashboard
