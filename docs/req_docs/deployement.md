This deployment guide bridges the gap between your local laptop and the public internet, ensuring a smooth flow for both "Vibe Coding" (speed) and "Enterprise Reliability" (uptime).

### 1. High-Level Topology

We use a **GitOps** workflow. Your Monorepo is the single source of truth.

| Component    | **Development (Local)**    | **Production (Live)**             |
| ------------ | -------------------------- | --------------------------------- |
| **Frontend** | `localhost:3000` (Next.js) | **Vercel** (`app.codewarden.io`)  |
| **Backend**  | `localhost:8000` (FastAPI) | **Railway** (`api.codewarden.io`) |
| **Database** | Supabase Local (Docker)    | **Supabase Cloud** (Managed)      |
| **Queue**    | Redis Local (Docker)       | **Upstash** (Serverless Redis)    |
| **Logs**     | OpenObserve Local (Docker) | **OpenObserve Cloud**             |
| **AI**       | LiteLLM Proxy (Local)      | LiteLLM Router (Railway Worker)   |

---

### 2. The Development Environment (Local)

**Goal:** Simulates the entire cloud infrastructure on one laptop using Docker.

**Setup:**
You will use a single `docker-compose.yml` file in the root of your Monorepo.

```yaml
# docker-compose.yml
version: "3.8"

services:
  # 1. The Database (Supabase Emulator)
  db:
    image: supabase/postgres
    ports: ["5432:5432"]

  # 2. The Job Queue (Redis)
  redis:
    image: redis:alpine
    ports: ["6379:6379"]

  # 3. Log Storage (OpenObserve)
  openobserve:
    image: openobserve/openobserve:latest
    ports: ["5080:5080"]
    environment:
      - ZO_ROOT_USER_EMAIL=admin@localhost
      - ZO_ROOT_USER_PASSWORD=admin

  # 4. The Backend API (FastAPI)
  api:
    build: ./api
    command: uvicorn main:app --reload --host 0.0.0.0
    volumes:
      - ./api:/app # Hot-reloading enabled
    ports: ["8000:8000"]
    depends_on: [db, redis]

  # 5. The Dashboard (Next.js)
  dashboard:
    build: ./dashboard
    command: npm run dev
    volumes:
      - ./dashboard:/app
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Workflow:**

1. Run `docker-compose up`.
2. Edit files in `/api` or `/dashboard`.
3. Changes reflect instantly (Hot Reloading).
4. Logs appear in local OpenObserve (`http://localhost:5080`).

---

### 3. The Production Environment (Live)

**Goal:** Automated, zero-downtime deployments triggered by Git pushes.

#### A. Backend Deployment (Railway)

- **Trigger:** Push to `main` branch.
- **Service 1 (API):** Hosts the FastAPI server.
- _Build Command:_ `pip install -r requirements.txt`
- _Start Command:_ `uvicorn main:app --host 0.0.0.0 --port $PORT`

- **Service 2 (Worker):** Hosts the Background Job Processor.
- _Start Command:_ `arq worker.WorkerSettings`

- **Secrets:** Managed in Railway Dashboard (not `.env` files).
- `SUPABASE_URL`
- `OPENAI_API_KEY`
- `LITELLM_MASTER_KEY`

#### B. Frontend Deployment (Vercel)

- **Trigger:** Push to `main` branch.
- **Configuration:** Vercel automatically detects Next.js.
- **Environment Variables:**
- `NEXT_PUBLIC_API_URL`: `https://api.codewarden.io`
- `NEXT_PUBLIC_SUPABASE_URL`: `https://xyz.supabase.co`

#### C. Data Layer (Supabase & OpenObserve)

- **Supabase:** You do **not** deploy this yourself. You use their managed cloud.
- _Migration Strategy:_ Use `supabase-cli` in GitHub Actions to apply SQL changes to the production DB on deploy.

- **OpenObserve:** You can either self-host on a cheap VPS (e.g., Hetzner) for $5/mo or use their Cloud Free Tier.
- _Recommendation:_ Start with Cloud Free Tier to save DevOps time.

---

### 4. CI/CD Pipeline (GitHub Actions)

We automate the "chore" work so you can just code.

**File:** `.github/workflows/deploy.yml`

```yaml
name: Production Deploy

on:
  push:
    branches: [main]

jobs:
  # 1. Quality Gate (Must pass before deploying)
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Backend Tests
        run: |
          pip install -r api/requirements.txt
          pytest api/tests
      - name: Run Frontend Lint
        run: |
          cd dashboard && npm install && npm run lint

  # 2. Migration (Update DB Schema)
  migrate:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: supabase/setup-cli@v1
      - run: supabase db push --linked # Applies SQL changes to Prod

  # 3. Publish SDKs (Only if a new Release Tag is created)
  publish-sdk:
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    steps:
      - name: Publish to PyPI
        run: hatch publish
        env:
          HATCH_INDEX_USER: __token__
          HATCH_INDEX_AUTH: ${{ secrets.PYPI_TOKEN }}
```

### 5. Summary Checklist

| Environment | URL             | Deployed Via              | Data Source              |
| ----------- | --------------- | ------------------------- | ------------------------ |
| **Dev**     | `localhost`     | Docker Compose            | Local Postgres & Redis   |
| **Prod**    | `codewarden.io` | Git Push (Railway/Vercel) | Supabase Cloud & Upstash |
| **SDKs**    | `pip install`   | GitHub Release Tag        | PyPI / NPM Registry      |

**Strategic Note:**
This setup allows you to fix a bug locally, push to Git, and have the fix live in production **within 3 minutes** without touching a server manually. This speed is your competitive advantage.

Based on the **Technical PRD** and **Master Build Plan**, here is the exact deployment stack chosen for CodeWarden. This setup is designed for **speed**, **low cost** (free tiers), and **reliability**.

### 1. The Deployment Stack (Production)

You are using a **"Best-in-Class" Cloud Strategy** rather than putting everything on one server (like AWS EC2). This saves you from managing servers.

| Component              | Platform          | Why this choice?                                                                                                                                                                               |
| ---------------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Frontend Dashboard** | **Vercel**        | It is the native home of **Next.js**. It handles the "Edge" network, making your dashboard load fast globally.                                                                                 |
| **Backend API**        | **Railway**       | It is excellent for **Python/FastAPI**. Unlike Vercel (which has timeout limits on serverless functions), Railway allows your API to run continuously, which is needed for background workers. |
| **Database**           | **Supabase**      | It gives you a managed **Postgres** DB plus **Authentication** (Magic Links) out of the box. You don't have to write your own auth server.                                                     |
| **Job Queue (Redis)**  | **Upstash**       | It is "Serverless Redis." You pay only per request. Since you are just launching, this will likely be free, whereas a dedicated Redis instance costs ~$10/mo.                                  |
| **Log Storage**        | **OpenObserve**   | You need to store terabytes of logs cheaply. OpenObserve (Cloud or Self-Hosted) is significantly cheaper than Datadog or Splunk.                                                               |
| **Evidence Storage**   | **Cloudflare R2** | For storing the SOC 2 PDF exports. It has zero egress fees (unlike AWS S3), so downloading reports is free.                                                                                    |

---

### 2. How They Connect (The Topology)

This is how the pieces talk to each other in production.

1. **User** visits `codewarden.io` → Hits **Vercel** (Frontend).
2. **Frontend** needs data → Calls `api.codewarden.io` on **Railway**.
3. **API** needs to login user → Checks **Supabase**.
4. **SDK (User App)** sends a crash log → Hits **Railway** → Pushed to **Upstash** (Queue).
5. **Worker (Railway)** picks up log → Sends to **LiteLLM** (AI) → Saves to **OpenObserve**.

---

### 3. Quick Setup Guide

#### **Step A: The Database (Supabase)**

1. Go to `supabase.com` -> New Project.
2. Get your `DATABASE_URL` and `SUPABASE_SERVICE_KEY`.
3. **Cost:** Free (500MB storage is plenty for metadata).

#### **Step B: The Backend (Railway)**

1. Go to `railway.app` -> New Project -> Deploy from GitHub Repo (`/api` folder).
2. Add Variables: `SUPABASE_URL`, `OPENAI_API_KEY`, `REDIS_URL`.
3. **Cost:** ~$5/month (Railway Trial covers this initially).

#### **Step C: The Frontend (Vercel)**

1. Go to `vercel.com` -> New Project -> Import GitHub Repo (`/dashboard` folder).
2. Add Variables: `NEXT_PUBLIC_API_URL` (Your Railway URL).
3. **Cost:** Free (Hobby Tier).

### **Summary Recommendation**

Stick to **Vercel (Frontend)** + **Railway (Backend)**.
This combination prevents the common "Cold Start" issues with Python on Vercel and gives you a robust, scalable environment from Day 1.
