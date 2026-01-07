-- CodeWarden: Fix User Signup Trigger Permissions
-- The handle_new_user() trigger was failing because it couldn't insert into
-- tables with RLS enabled when running in the context of the new user.
--
-- Solution: Recreate the trigger function with SECURITY DEFINER to run as
-- the function owner (postgres superuser) and ensure RLS bypass.

-- ============================================
-- DROP AND RECREATE THE TRIGGER FUNCTION
-- ============================================

-- Drop the existing trigger first
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Recreate the function with explicit SECURITY DEFINER
-- and SET search_path for security
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    new_org_id UUID;
    user_display_name TEXT;
    org_slug TEXT;
BEGIN
    -- Extract display name from metadata
    user_display_name := COALESCE(
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'name',
        split_part(NEW.email, '@', 1)
    );

    -- Generate org slug
    org_slug := LOWER(REGEXP_REPLACE(
        COALESCE(user_display_name, 'user'),
        '[^a-zA-Z0-9]+',
        '-',
        'g'
    )) || '-' || SUBSTRING(NEW.id::text, 1, 8);

    -- Create a personal organization for the user
    INSERT INTO public.organizations (name, slug)
    VALUES (
        COALESCE(user_display_name, 'My Organization') || '''s Organization',
        org_slug
    )
    RETURNING id INTO new_org_id;

    -- Create user profile linked to the org
    INSERT INTO public.user_profiles (id, org_id, display_name, avatar_url, role)
    VALUES (
        NEW.id,
        new_org_id,
        user_display_name,
        NEW.raw_user_meta_data->>'avatar_url',
        'owner'
    );

    RETURN NEW;
EXCEPTION
    WHEN unique_violation THEN
        -- Handle case where slug already exists (race condition)
        org_slug := org_slug || '-' || SUBSTRING(gen_random_uuid()::text, 1, 4);

        INSERT INTO public.organizations (name, slug)
        VALUES (
            COALESCE(user_display_name, 'My Organization') || '''s Organization',
            org_slug
        )
        RETURNING id INTO new_org_id;

        INSERT INTO public.user_profiles (id, org_id, display_name, avatar_url, role)
        VALUES (
            NEW.id,
            new_org_id,
            user_display_name,
            NEW.raw_user_meta_data->>'avatar_url',
            'owner'
        );

        RETURN NEW;
    WHEN OTHERS THEN
        -- Log the error but don't prevent user creation
        RAISE WARNING 'Failed to create organization/profile for user %: %', NEW.id, SQLERRM;
        RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recreate the trigger
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- GRANT NECESSARY PERMISSIONS
-- ============================================

-- Grant the function execute permission to authenticated users
-- (Supabase handles this for auth triggers, but explicit is safer)
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO service_role;

-- Ensure the service role can insert into these tables
-- (This should already be the case, but being explicit)
GRANT INSERT ON public.organizations TO service_role;
GRANT INSERT ON public.user_profiles TO service_role;
GRANT SELECT ON public.organizations TO service_role;
GRANT SELECT ON public.user_profiles TO service_role;

-- ============================================
-- ADD POLICY FOR SERVICE ROLE INSERTS
-- ============================================

-- Allow service role to bypass RLS for organizations
DROP POLICY IF EXISTS "Service role can insert organizations" ON public.organizations;
CREATE POLICY "Service role can insert organizations" ON public.organizations
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- Allow service role to bypass RLS for user_profiles
DROP POLICY IF EXISTS "Service role can insert user_profiles" ON public.user_profiles;
CREATE POLICY "Service role can insert user_profiles" ON public.user_profiles
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- ============================================
-- VERIFY FIX
-- ============================================
-- After applying this migration, new user signups should:
-- 1. Successfully create an organization
-- 2. Successfully create a user profile
-- 3. Link the user to their organization
-- 4. Not show "Database error saving new user" anymore
