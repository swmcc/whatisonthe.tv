"""Application configuration."""

import os
from pathlib import Path
from typing import Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the backend directory (parent of app/core/)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
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

    # CORS - can be a comma-separated string or list
    cors_origins: Union[list[str], str] = "http://localhost:5173,http://localhost:5174,http://localhost:3000"

    # Security
    secret_key: str = "your-secret-key-change-in-production-min-32-chars-long"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # LLM Configuration
    llm_provider: str = "anthropic"  # "anthropic" or "openai"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = "claude-sonnet-4-20250514"  # or "gpt-4o-mini" for OpenAI

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

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


settings = Settings()
