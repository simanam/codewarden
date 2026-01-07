# CodeWarden Supabase Database Setup

This directory contains the database schema and migrations for CodeWarden.

## Quick Setup

### 1. Apply the Initial Schema

1. Go to your Supabase Dashboard: https://supabase.com/dashboard/project/_/sql
2. Open the SQL Editor
3. Copy and paste the contents of `migrations/20260104_initial_schema.sql`
4. Click "Run"

### 2. Verify the Setup

After running the migration, you should see these tables:
- `organizations` - User organizations (workspaces)
- `user_profiles` - Extended user profiles (links to auth.users)
- `apps` - Applications/projects being monitored
- `api_keys` - API keys for SDK authentication
- `event_metadata` - Error/event metadata (logs stored in OpenObserve)
- `evidence_events` - SOC 2 compliance evidence
- `security_scans` - Vulnerability scan results
- `pairing_sessions` - SDK pairing sessions (Telegram/Email)
- `notifications` - User notifications
- `daily_briefs` - Daily summary emails

### 3. Key Features

#### Auto User Profile Creation
When a user signs up (via OAuth or Magic Link), the system automatically:
1. Creates a personal organization for them
2. Creates a user profile linked to that org
3. Sets them as the organization owner

#### Row Level Security (RLS)
All tables have RLS enabled:
- Users can only see data from their organization
- API server uses `service_role` key to bypass RLS for telemetry ingestion

#### API Key Authentication
API keys follow the format: `cw_live_aBcDeFgHiJkLmNoPqRsT` or `cw_test_...`
- `live` keys work in production
- `test` keys work in development

## Database Schema

```
┌─────────────────┐     ┌─────────────────┐
│  organizations  │────<│  user_profiles  │
└────────┬────────┘     └─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐     ┌─────────────────┐
│      apps       │────<│    api_keys     │
└────────┬────────┘     └─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐     ┌─────────────────┐
│ event_metadata  │     │ evidence_events │
└─────────────────┘     └─────────────────┘
         │
         │
         ▼
┌─────────────────┐
│ security_scans  │
└─────────────────┘
```

## Environment Variables

Add these to your `.env` file:

```bash
# Get from: https://supabase.com/dashboard/project/_/settings/api
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key  # For API server only
```

## Resetting the Database

To reset everything and start fresh:

```sql
-- WARNING: This deletes ALL data!
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
```

Then re-run the migration SQL.

## Adding New Migrations

Create new migration files with the naming convention:
```
YYYYMMDD_description.sql
```

Example: `20260110_add_webhooks.sql`

## Safe Migration Practices (Production)

When you have customers with data, follow these rules:

### DO:
- **Add new columns** with `DEFAULT` values or as `NULLABLE`
- **Add new tables** freely
- **Add indexes** (non-blocking with `CONCURRENTLY`)
- **Add new functions/triggers**
- **Rename with views** - create a view with old name pointing to new

### DON'T:
- **Drop columns** - mark as deprecated, remove later
- **Drop tables** - archive/soft-delete instead
- **Rename columns directly** - use views or add new + migrate + drop old
- **Change column types** - add new column, migrate data, drop old

### Migration Template:
```sql
-- Migration: YYYYMMDD_description.sql
-- Description: What this migration does
-- Rollback: How to undo if needed

BEGIN;

-- Your changes here

COMMIT;
```

### Example: Safe Column Rename
```sql
-- Instead of: ALTER TABLE apps RENAME COLUMN name TO title;
-- Do this:

-- Step 1: Add new column
ALTER TABLE apps ADD COLUMN title TEXT;

-- Step 2: Copy data
UPDATE apps SET title = name;

-- Step 3: Make it required
ALTER TABLE apps ALTER COLUMN title SET NOT NULL;

-- Step 4: Create view for backwards compatibility (optional)
CREATE VIEW apps_v1 AS SELECT *, name AS old_name FROM apps;

-- Step 5: In a LATER migration (after all code updated):
-- ALTER TABLE apps DROP COLUMN name;
```

## CI/CD Migration Setup

Migrations run automatically on push to `main` via GitHub Actions.

### Required Secrets:
1. `SUPABASE_PROJECT_ID` - From Supabase Dashboard → Settings → General
2. `SUPABASE_ACCESS_TOKEN` - From https://supabase.com/dashboard/account/tokens

### Manual Migration (if CI fails):
```bash
# Install Supabase CLI
brew install supabase/tap/supabase

# Link to your project
cd packages/api
supabase link --project-ref YOUR_PROJECT_ID

# Push migrations
supabase db push
```

### Verify Migrations Applied:
```sql
-- Check migration history
SELECT * FROM supabase_migrations.schema_migrations ORDER BY version DESC;
```
