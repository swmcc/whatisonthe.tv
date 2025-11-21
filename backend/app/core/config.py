"""Application configuration."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # Don't try to parse cors_origins from env automatically
        env_ignore=["cors_origins"],
    )

    # Application
    app_name: str = "WatchLog"
    debug: bool = False
    version: str = "0.1.0"

    # Database
    database_url: str = "postgresql+asyncpg://watchlog:watchlog@localhost:5432/watchlog"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # TVDB API
    tvdb_api_key: str = ""
    tvdb_pin: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]

    # Security
    secret_key: str = "your-secret-key-change-in-production-min-32-chars-long"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    def __init__(self, **kwargs):
        """Initialize settings with Heroku environment variable support."""
        super().__init__(**kwargs)

        # Heroku provides DATABASE_URL for Postgres
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            # Heroku uses postgres://, SQLAlchemy 1.4+ requires postgresql://
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            # Add asyncpg driver
            if "postgresql://" in db_url and "+asyncpg" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            self.database_url = db_url

        # Heroku provides REDIS_URL for Redis
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            self.redis_url = redis_url

        # Parse CORS origins from comma-separated string (for Heroku config)
        cors_env = os.getenv("CORS_ORIGINS")
        if cors_env and cors_env.strip():
            self.cors_origins = [origin.strip() for origin in cors_env.split(",")]


settings = Settings()
