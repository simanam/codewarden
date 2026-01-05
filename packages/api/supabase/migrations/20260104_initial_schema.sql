-- CodeWarden Initial Database Schema
-- Based on Technical PRD v1.0
--
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/_/sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- ORGANIZATIONS
-- ============================================
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    plan TEXT DEFAULT 'hobbyist' CHECK (plan IN ('hobbyist', 'builder', 'pro', 'team', 'enterprise')),
    plan_limits JSONB DEFAULT '{
        "events_per_month": 1000,
        "apps_limit": 1,
        "retention_days": 7
    }'::jsonb,
    billing_email TEXT,
    stripe_customer_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create slug from name trigger
CREATE OR REPLACE FUNCTION generate_slug()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.slug IS NULL OR NEW.slug = '' THEN
        NEW.slug := LOWER(REGEXP_REPLACE(NEW.name, '[^a-zA-Z0-9]+', '-', 'g'));
        -- Ensure uniqueness by appending random suffix if needed
        WHILE EXISTS (SELECT 1 FROM organizations WHERE slug = NEW.slug AND id != NEW.id) LOOP
            NEW.slug := NEW.slug || '-' || SUBSTRING(uuid_generate_v4()::text, 1, 4);
        END LOOP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_org_slug
    BEFORE INSERT ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION generate_slug();

-- ============================================
-- USERS (extends Supabase auth.users)
-- ============================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    display_name TEXT,
    avatar_url TEXT,
    telegram_chat_id TEXT,
    notification_preferences JSONB DEFAULT '{
        "email": true,
        "telegram": false,
        "daily_brief": true,
        "critical_alerts": true
    }'::jsonb,
    role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- APPLICATIONS (Projects)
-- ============================================
CREATE TABLE IF NOT EXISTS apps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT,
    environment TEXT DEFAULT 'production' CHECK (environment IN ('development', 'staging', 'production')),
    framework TEXT, -- 'fastapi', 'nextjs', 'express', etc.
    last_event_at TIMESTAMPTZ,
    last_seen_at TIMESTAMPTZ,
    config JSONB DEFAULT '{
        "scrub_pii": true,
        "scan_on_startup": true,
        "notify_on_crash": true,
        "evidence_logging": true
    }'::jsonb,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'archived')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, slug)
);

-- ============================================
-- API KEYS
-- ============================================
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    app_id UUID REFERENCES apps(id) ON DELETE CASCADE,

    -- Key storage (we store hash, prefix shown to user)
    key_hash TEXT UNIQUE NOT NULL,
    key_prefix TEXT NOT NULL, -- e.g., "cw_live_aBcD" (first 12 chars)

    -- Metadata
    name TEXT NOT NULL DEFAULT 'Default Key',
    key_type TEXT DEFAULT 'live' CHECK (key_type IN ('live', 'test')),

    -- Permissions
    permissions JSONB DEFAULT '["telemetry:write", "evidence:write", "health:read"]'::jsonb,

    -- Usage tracking
    last_used_at TIMESTAMPTZ,
    usage_count BIGINT DEFAULT 0,

    -- Lifecycle
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_org ON api_keys(org_id);
CREATE INDEX idx_api_keys_app ON api_keys(app_id);

-- ============================================
-- EVENT METADATA
-- (Actual logs stored in OpenObserve, this is for quick lookups)
-- ============================================
CREATE TABLE IF NOT EXISTS event_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,

    -- Event identification
    event_type TEXT NOT NULL CHECK (event_type IN ('crash', 'error', 'warning', 'info', 'security', 'performance')),
    trace_id TEXT,

    -- Quick-access fields (denormalized for dashboard queries)
    severity TEXT CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    error_type TEXT,
    error_message TEXT,
    file_path TEXT,
    line_number INTEGER,

    -- AI Analysis
    analysis_status TEXT DEFAULT 'pending' CHECK (analysis_status IN ('pending', 'processing', 'completed', 'failed')),
    analysis_result JSONB,
    model_used TEXT,
    analyzed_at TIMESTAMPTZ,

    -- OpenObserve reference
    openobserve_id TEXT,

    -- Timestamps
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Resolution tracking
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'resolved', 'ignored')),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES auth.users(id)
);

CREATE INDEX idx_events_app ON event_metadata(app_id);
CREATE INDEX idx_events_created ON event_metadata(created_at DESC);
CREATE INDEX idx_events_severity ON event_metadata(severity);
CREATE INDEX idx_events_status ON event_metadata(status);
CREATE INDEX idx_events_trace ON event_metadata(trace_id);

-- ============================================
-- EVIDENCE LOCKER (SOC 2 Compliance)
-- ============================================
CREATE TABLE IF NOT EXISTS evidence_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,

    -- Event categorization
    event_type TEXT NOT NULL CHECK (event_type IN (
        'AUDIT_DEPLOY',      -- Deployment records
        'AUDIT_SCAN',        -- Security scan results
        'AUDIT_ACCESS',      -- Authentication events
        'AUDIT_CONFIG',      -- Configuration changes
        'AUDIT_EXPORT',      -- Evidence exports
        'AUDIT_INCIDENT'     -- Security incidents
    )),

    -- Event data (flexible schema per type)
    data JSONB NOT NULL,

    -- Audit trail
    actor_id UUID REFERENCES auth.users(id),
    actor_email TEXT,
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_evidence_app_type ON evidence_events(app_id, event_type);
CREATE INDEX idx_evidence_created ON evidence_events(created_at DESC);
CREATE INDEX idx_evidence_type ON evidence_events(event_type);

-- ============================================
-- SECURITY SCANS
-- ============================================
CREATE TABLE IF NOT EXISTS security_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,

    -- Scan details
    scan_type TEXT NOT NULL CHECK (scan_type IN ('dependencies', 'secrets', 'code', 'full')),
    tool_name TEXT NOT NULL, -- 'pip-audit', 'npm-audit', 'bandit', 'gitleaks'

    -- Results
    status TEXT DEFAULT 'running' CHECK (status IN ('running', 'passed', 'failed', 'error')),
    vulnerability_count INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,

    -- Detailed findings
    findings JSONB DEFAULT '[]'::jsonb,
    fix_commands JSONB DEFAULT '[]'::jsonb,

    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER
);

CREATE INDEX idx_scans_app ON security_scans(app_id);
CREATE INDEX idx_scans_created ON security_scans(started_at DESC);

-- ============================================
-- PAIRING SESSIONS (for SDK setup)
-- ============================================
CREATE TABLE IF NOT EXISTS pairing_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Pairing method
    method TEXT NOT NULL CHECK (method IN ('telegram', 'email')),

    -- Identifiers
    pairing_code TEXT UNIQUE, -- For telegram: "CW-1234"
    email TEXT,               -- For email magic link
    token TEXT UNIQUE,        -- Magic link token

    -- Telegram specific
    telegram_chat_id TEXT,
    telegram_username TEXT,

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'expired', 'used')),
    verified_at TIMESTAMPTZ,

    -- Link to user/org after verification
    user_id UUID REFERENCES auth.users(id),
    org_id UUID REFERENCES organizations(id),
    app_id UUID REFERENCES apps(id),

    -- Generated API key
    api_key_id UUID REFERENCES api_keys(id),

    -- Expiration
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pairing_code ON pairing_sessions(pairing_code);
CREATE INDEX idx_pairing_token ON pairing_sessions(token);
CREATE INDEX idx_pairing_status ON pairing_sessions(status);

-- ============================================
-- NOTIFICATIONS
-- ============================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Content
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    type TEXT DEFAULT 'info' CHECK (type IN ('info', 'warning', 'error', 'success')),

    -- Related entities
    app_id UUID REFERENCES apps(id) ON DELETE CASCADE,
    event_id UUID REFERENCES event_metadata(id) ON DELETE CASCADE,

    -- Delivery
    channels_sent JSONB DEFAULT '[]'::jsonb, -- ['email', 'telegram', 'push']

    -- Status
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id) WHERE read_at IS NULL;

-- ============================================
-- DAILY BRIEFS
-- ============================================
CREATE TABLE IF NOT EXISTS daily_briefs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Brief data
    date DATE NOT NULL,
    summary JSONB NOT NULL, -- {error_count, warning_count, request_count, uptime, security_status, action_items}

    -- Delivery
    sent_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE apps ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_briefs ENABLE ROW LEVEL SECURITY;

-- User profiles: users can only see/edit their own profile
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Organizations: users can see their org
CREATE POLICY "Users can view their organization" ON organizations
    FOR SELECT USING (
        id IN (SELECT org_id FROM user_profiles WHERE id = auth.uid())
    );

CREATE POLICY "Org owners can update organization" ON organizations
    FOR UPDATE USING (
        id IN (SELECT org_id FROM user_profiles WHERE id = auth.uid() AND role = 'owner')
    );

-- Apps: users can see apps in their org
CREATE POLICY "Users can view org apps" ON apps
    FOR SELECT USING (
        org_id IN (SELECT org_id FROM user_profiles WHERE id = auth.uid())
    );

CREATE POLICY "Users can create apps in their org" ON apps
    FOR INSERT WITH CHECK (
        org_id IN (SELECT org_id FROM user_profiles WHERE id = auth.uid())
    );

CREATE POLICY "Users can update org apps" ON apps
    FOR UPDATE USING (
        org_id IN (SELECT org_id FROM user_profiles WHERE id = auth.uid())
    );

-- API Keys: users can see keys in their org
CREATE POLICY "Users can view org api keys" ON api_keys
    FOR SELECT USING (
        org_id IN (SELECT org_id FROM user_profiles WHERE id = auth.uid())
    );

CREATE POLICY "Users can create api keys in their org" ON api_keys
    FOR INSERT WITH CHECK (
        org_id IN (SELECT org_id FROM user_profiles WHERE id = auth.uid())
    );

-- Events: users can see events from their org's apps
CREATE POLICY "Users can view org events" ON event_metadata
    FOR SELECT USING (
        app_id IN (
            SELECT id FROM apps WHERE org_id IN (
                SELECT org_id FROM user_profiles WHERE id = auth.uid()
            )
        )
    );

-- Evidence: users can see evidence from their org's apps
CREATE POLICY "Users can view org evidence" ON evidence_events
    FOR SELECT USING (
        app_id IN (
            SELECT id FROM apps WHERE org_id IN (
                SELECT org_id FROM user_profiles WHERE id = auth.uid()
            )
        )
    );

-- Security scans: users can see scans from their org's apps
CREATE POLICY "Users can view org scans" ON security_scans
    FOR SELECT USING (
        app_id IN (
            SELECT id FROM apps WHERE org_id IN (
                SELECT org_id FROM user_profiles WHERE id = auth.uid()
            )
        )
    );

-- Notifications: users can only see their own
CREATE POLICY "Users can view own notifications" ON notifications
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can update own notifications" ON notifications
    FOR UPDATE USING (user_id = auth.uid());

-- Daily briefs: users can only see their own
CREATE POLICY "Users can view own briefs" ON daily_briefs
    FOR SELECT USING (user_id = auth.uid());

-- ============================================
-- SERVICE ROLE BYPASS (for API server)
-- ============================================
-- The API server uses service_role key which bypasses RLS
-- This is intentional for SDK telemetry ingestion

-- ============================================
-- UPDATED_AT TRIGGER
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_apps_updated_at
    BEFORE UPDATE ON apps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- AUTO-CREATE USER PROFILE ON SIGNUP
-- ============================================
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    new_org_id UUID;
BEGIN
    -- Create a personal organization for the user
    INSERT INTO organizations (name, slug)
    VALUES (
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email, 'My Organization'),
        LOWER(REGEXP_REPLACE(COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)), '[^a-zA-Z0-9]+', '-', 'g')) || '-' || SUBSTRING(NEW.id::text, 1, 8)
    )
    RETURNING id INTO new_org_id;

    -- Create user profile linked to the org
    INSERT INTO user_profiles (id, org_id, display_name, avatar_url, role)
    VALUES (
        NEW.id,
        new_org_id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name'),
        NEW.raw_user_meta_data->>'avatar_url',
        'owner'
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Generate API key (called from API server, not directly)
CREATE OR REPLACE FUNCTION generate_api_key_prefix(key_type TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN 'cw_' || key_type || '_' || SUBSTRING(encode(gen_random_bytes(16), 'base64'), 1, 24);
END;
$$ LANGUAGE plpgsql;

-- Get app by API key hash (used by API for auth)
CREATE OR REPLACE FUNCTION get_app_by_api_key(p_key_hash TEXT)
RETURNS TABLE (
    app_id UUID,
    org_id UUID,
    app_name TEXT,
    org_plan TEXT,
    permissions JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id AS app_id,
        a.org_id,
        a.name AS app_name,
        o.plan AS org_plan,
        k.permissions
    FROM api_keys k
    JOIN apps a ON k.app_id = a.id
    JOIN organizations o ON a.org_id = o.id
    WHERE k.key_hash = p_key_hash
    AND k.revoked_at IS NULL
    AND (k.expires_at IS NULL OR k.expires_at > NOW());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Increment API key usage counter
CREATE OR REPLACE FUNCTION increment_api_key_usage(p_key_hash TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE api_keys
    SET
        usage_count = usage_count + 1,
        last_used_at = NOW()
    WHERE key_hash = p_key_hash;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
