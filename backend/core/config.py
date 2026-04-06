from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
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
    allowed_origins_str: str = "http://localhost,http://localhost:5173"

    @computed_field
    @property
    def allowed_origins(self) -> list[str]:
        """Parse comma-separated ALLOWED_ORIGINS_STR into list."""
        return [origin.strip() for origin in self.allowed_origins_str.split(",") if origin.strip()]

    # Database
    database_url: str = "postgresql+asyncpg://a11y:a11ypass@postgres:5432/accessibility_db"

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
