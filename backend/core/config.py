import re

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field, Field
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Accessibility Evaluation Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # CORS origins as comma-separated string (parsed by property)
    allowed_origins_str: str = "http://localhost,http://localhost:5173,https://accessibility-platform-hazel.vercel.app,https://accessibility-platform-git-main-antaripdebguptas-projects.vercel.app,https://accessibility-platform-antaripdebguptas-projects.vercel.app"

    @computed_field
    @property
    def allowed_origins(self) -> list[str]:
        """Parse comma-separated ALLOWED_ORIGINS_STR into list."""
        return [origin.strip() for origin in self.allowed_origins_str.split(",") if origin.strip()]

    # Database — raw value from env var / .env (may use any postgres scheme)
    # Reads from DATABASE_URL env var, but stored as database_url_raw to leave
    # the computed "database_url" property free for the normalised async URL.
    database_url_raw: str = Field(
        default="postgresql+asyncpg://a11y:a11ypass@postgres:5432/accessibility_db",
        validation_alias="DATABASE_URL",
    )

    @computed_field
    @property
    def database_url(self) -> str:
        """Normalise DATABASE_URL to always use the asyncpg driver.

        Neon / Render / Supabase typically provide URLs like:
            postgresql://user:pass@host/db?sslmode=require
            postgres://user:pass@host/db
        SQLAlchemy's create_async_engine with asyncpg needs:
            postgresql+asyncpg://user:pass@host/db?ssl=require

        Note: asyncpg uses 'ssl' parameter, not 'sslmode'.
        """
        url = self.database_url_raw
        # Replace any postgres(ql) scheme (with or without a +driver) with postgresql+asyncpg
        url = re.sub(r"^postgres(ql)?(\+\w+)?://", "postgresql+asyncpg://", url)
        # Convert sslmode to ssl for asyncpg compatibility
        url = url.replace("sslmode=", "ssl=")
        # Remove parameters not supported by asyncpg (e.g. channel_binding from Neon)
        url = re.sub(r"[&?]channel_binding=[^&]*", "", url)
        return url

    # Redis
    redis_url: str = "redis://redis:6379/0"


    # Firebase
    firebase_project_id: str = ""
    firebase_service_account_key: str = "/run/secrets/firebase_sa.json"

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_external_endpoint: str = "localhost"  # External endpoint via nginx proxy
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_reports: str = "reports"
    minio_bucket_screenshots: str = "screenshots"
    minio_secure: bool = False

    # Crawler
    default_max_pages: int = 15
    crawler_timeout_ms: int = 30000

    # Email / SMTP
    smtp_host: str = ""  # Empty or "disabled" skips sending emails
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@a11y-platform.dev"

    # Frontend URL for invitation links
    frontend_url: str = "http://localhost"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
