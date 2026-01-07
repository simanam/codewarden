"""Supabase database client for CodeWarden API."""

from functools import lru_cache

from api.config import settings
from supabase import Client, create_client


@lru_cache
def get_supabase_client() -> Client:
    """Get cached Supabase client using service role key.

    The service role key bypasses Row Level Security (RLS),
    which is needed for the API to process telemetry from SDKs.
    """
    url = settings.supabase_url
    key = settings.supabase_private_key

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SECRET_KEY (or SUPABASE_SERVICE_KEY) "
            "must be set in environment variables"
        )

    return create_client(url, key)


# Singleton instance
supabase = get_supabase_client() if settings.supabase_private_key else None
