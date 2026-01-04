"""CodeWarden API Configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App settings
    app_name: str = "CodeWarden API"
    environment: str = "development"
    debug: bool = True
    log_level: str = "debug"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    supabase_url: str = "http://localhost:8000"

    # NEW Supabase API Keys (2025+) - preferred
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""

    # LEGACY Supabase API Keys (deprecated, for backwards compatibility)
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    @property
    def supabase_public_key(self) -> str:
        """Get the public key (new publishable or legacy anon)."""
        return self.supabase_publishable_key or self.supabase_anon_key

    @property
    def supabase_private_key(self) -> str:
        """Get the private key (new secret or legacy service_role)."""
        return self.supabase_secret_key or self.supabase_service_key

    # Redis
    redis_url: str = "redis://localhost:6379"

    # OpenObserve
    openobserve_url: str = "http://localhost:5080"
    openobserve_org: str = "default"
    openobserve_user: str = "admin@codewarden.local"
    openobserve_password: str = "admin123"

    # AI Providers
    google_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Notifications
    resend_api_key: str = ""
    telegram_bot_token: str = ""

    # Storage
    cloudflare_r2_access_key_id: str = ""
    cloudflare_r2_secret_access_key: str = ""
    cloudflare_r2_bucket: str = "codewarden-evidence"
    cloudflare_r2_endpoint: str = ""


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
