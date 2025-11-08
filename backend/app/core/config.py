"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
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

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]

    # Security
    secret_key: str = "your-secret-key-change-in-production-min-32-chars-long"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days


settings = Settings()
