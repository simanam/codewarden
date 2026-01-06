-- CodeWarden: Add Admin and Partner Tiers
-- Admin: Full access to all features without any restrictions
-- Partner: Highest paid tier (enterprise) features for free

-- ============================================
-- UPDATE ORGANIZATIONS TABLE
-- ============================================

-- Drop existing constraint and add new one with admin and partner tiers
ALTER TABLE organizations
DROP CONSTRAINT IF EXISTS organizations_plan_check;

ALTER TABLE organizations
ADD CONSTRAINT organizations_plan_check
CHECK (plan IN ('hobbyist', 'builder', 'pro', 'team', 'enterprise', 'partner', 'admin'));

-- ============================================
-- PLAN LIMITS REFERENCE
-- ============================================
-- Define plan limits for reference (used by application layer):
--
-- hobbyist (free):
--   events_per_month: 1,000
--   apps_limit: 1
--   retention_days: 7
--   ai_analysis: false
--   security_scans: false
--
-- builder ($19/mo):
--   events_per_month: 10,000
--   apps_limit: 3
--   retention_days: 30
--   ai_analysis: true
--   security_scans: basic
--
-- pro ($49/mo):
--   events_per_month: 50,000
--   apps_limit: 10
--   retention_days: 90
--   ai_analysis: true
--   security_scans: full
--   evidence_locker: true
--
-- team ($99/mo):
--   events_per_month: 200,000
--   apps_limit: 25
--   retention_days: 180
--   ai_analysis: true
--   security_scans: full
--   evidence_locker: true
--   team_members: 10
--
-- enterprise (custom):
--   events_per_month: unlimited
--   apps_limit: unlimited
--   retention_days: 365
--   ai_analysis: true
--   security_scans: full
--   evidence_locker: true
--   team_members: unlimited
--   sso: true
--   dedicated_support: true
--
-- partner (free - same as enterprise):
--   All enterprise features for free
--   Special partner badge in dashboard
--   Priority support
--
-- admin (internal):
--   No restrictions whatsoever
--   Access to all organizations
--   System administration capabilities
--   Bypass all rate limits

-- ============================================
-- HELPER FUNCTION: GET PLAN LIMITS
-- ============================================
CREATE OR REPLACE FUNCTION get_plan_limits(p_plan TEXT)
RETURNS JSONB AS $$
BEGIN
    RETURN CASE p_plan
        WHEN 'hobbyist' THEN '{
            "events_per_month": 1000,
            "apps_limit": 1,
            "retention_days": 7,
            "ai_analysis": false,
            "security_scans": false,
            "evidence_locker": false,
            "team_members": 1,
            "is_paid": false
        }'::jsonb
        WHEN 'builder' THEN '{
            "events_per_month": 10000,
            "apps_limit": 3,
            "retention_days": 30,
            "ai_analysis": true,
            "security_scans": "basic",
            "evidence_locker": false,
            "team_members": 1,
            "is_paid": true
        }'::jsonb
        WHEN 'pro' THEN '{
            "events_per_month": 50000,
            "apps_limit": 10,
            "retention_days": 90,
            "ai_analysis": true,
            "security_scans": "full",
            "evidence_locker": true,
            "team_members": 3,
            "is_paid": true
        }'::jsonb
        WHEN 'team' THEN '{
            "events_per_month": 200000,
            "apps_limit": 25,
            "retention_days": 180,
            "ai_analysis": true,
            "security_scans": "full",
            "evidence_locker": true,
            "team_members": 10,
            "is_paid": true
        }'::jsonb
        WHEN 'enterprise' THEN '{
            "events_per_month": -1,
            "apps_limit": -1,
            "retention_days": 365,
            "ai_analysis": true,
            "security_scans": "full",
            "evidence_locker": true,
            "team_members": -1,
            "sso": true,
            "dedicated_support": true,
            "is_paid": true
        }'::jsonb
        WHEN 'partner' THEN '{
            "events_per_month": -1,
            "apps_limit": -1,
            "retention_days": 365,
            "ai_analysis": true,
            "security_scans": "full",
            "evidence_locker": true,
            "team_members": -1,
            "sso": true,
            "dedicated_support": true,
            "priority_support": true,
            "partner_badge": true,
            "is_paid": false
        }'::jsonb
        WHEN 'admin' THEN '{
            "events_per_month": -1,
            "apps_limit": -1,
            "retention_days": -1,
            "ai_analysis": true,
            "security_scans": "full",
            "evidence_locker": true,
            "team_members": -1,
            "sso": true,
            "dedicated_support": true,
            "admin_access": true,
            "bypass_rate_limits": true,
            "system_admin": true,
            "is_paid": false
        }'::jsonb
        ELSE '{
            "events_per_month": 1000,
            "apps_limit": 1,
            "retention_days": 7,
            "ai_analysis": false,
            "security_scans": false,
            "evidence_locker": false,
            "team_members": 1,
            "is_paid": false
        }'::jsonb
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================
-- HELPER FUNCTION: CHECK IF PLAN HAS FEATURE
-- ============================================
CREATE OR REPLACE FUNCTION plan_has_feature(p_plan TEXT, p_feature TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    limits JSONB;
    feature_value JSONB;
BEGIN
    -- Admin always has access to everything
    IF p_plan = 'admin' THEN
        RETURN TRUE;
    END IF;

    limits := get_plan_limits(p_plan);
    feature_value := limits->p_feature;

    -- Handle different types of feature values
    IF feature_value IS NULL THEN
        RETURN FALSE;
    ELSIF jsonb_typeof(feature_value) = 'boolean' THEN
        RETURN feature_value::boolean;
    ELSIF jsonb_typeof(feature_value) = 'string' THEN
        RETURN feature_value::text != 'false' AND feature_value::text != '';
    ELSIF jsonb_typeof(feature_value) = 'number' THEN
        RETURN (feature_value::int != 0);
    ELSE
        RETURN TRUE;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================
-- HELPER FUNCTION: CHECK IF WITHIN PLAN LIMITS
-- ============================================
CREATE OR REPLACE FUNCTION check_plan_limit(p_plan TEXT, p_limit_name TEXT, p_current_value INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    limits JSONB;
    limit_value INTEGER;
BEGIN
    -- Admin bypasses all limits
    IF p_plan = 'admin' THEN
        RETURN TRUE;
    END IF;

    limits := get_plan_limits(p_plan);
    limit_value := (limits->>p_limit_name)::integer;

    -- -1 means unlimited
    IF limit_value = -1 THEN
        RETURN TRUE;
    END IF;

    RETURN p_current_value < limit_value;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================
-- UPDATE get_app_by_api_key TO INCLUDE PLAN LIMITS
-- ============================================
-- Drop existing function first (return type changed)
DROP FUNCTION IF EXISTS get_app_by_api_key(TEXT);

CREATE OR REPLACE FUNCTION get_app_by_api_key(p_key_hash TEXT)
RETURNS TABLE (
    app_id UUID,
    org_id UUID,
    app_name TEXT,
    org_plan TEXT,
    plan_limits JSONB,
    permissions JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id AS app_id,
        a.org_id,
        a.name AS app_name,
        o.plan AS org_plan,
        get_plan_limits(o.plan) AS plan_limits,
        k.permissions
    FROM api_keys k
    JOIN apps a ON k.app_id = a.id
    JOIN organizations o ON a.org_id = o.id
    WHERE k.key_hash = p_key_hash
    AND k.revoked_at IS NULL
    AND (k.expires_at IS NULL OR k.expires_at > NOW());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- TRIGGER: AUTO-UPDATE PLAN LIMITS ON PLAN CHANGE
-- ============================================
CREATE OR REPLACE FUNCTION sync_plan_limits()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.plan IS DISTINCT FROM OLD.plan THEN
        NEW.plan_limits := get_plan_limits(NEW.plan);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS sync_org_plan_limits ON organizations;
CREATE TRIGGER sync_org_plan_limits
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    WHEN (NEW.plan IS DISTINCT FROM OLD.plan)
    EXECUTE FUNCTION sync_plan_limits();

-- ============================================
-- COMMENT FOR DOCUMENTATION
-- ============================================
COMMENT ON COLUMN organizations.plan IS 'User tier: hobbyist, builder, pro, team, enterprise, partner (free enterprise), admin (full access)';
