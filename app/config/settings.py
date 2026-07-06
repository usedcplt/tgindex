"""Application settings using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class TelegramSettings(BaseSettings):
    """Telegram API settings."""

    api_id: int = Field(..., description="Telegram API ID")
    api_hash: str = Field(..., description="Telegram API hash")
    session_name: str = Field("tgindex_session", description="Telethon session file name")
    session_string: str | None = Field(None, description="Telethon session string for cloud deployment")

    model_config = SettingsConfigDict(env_prefix="TELEGRAM_", env_file=str(ENV_FILE), extra="ignore")


class DatabaseSettings(BaseSettings):
    """Database settings."""

    url: str = Field(..., description="Database URL")
    pool_size: int = Field(2, description="Connection pool size")
    max_overflow: int = Field(1, description="Max pool overflow")
    pool_timeout: int = Field(30, description="Pool timeout in seconds")
    pool_recycle: int = Field(300, description="Pool recycle time in seconds")

    model_config = SettingsConfigDict(env_prefix="DATABASE_", env_file=str(ENV_FILE), extra="ignore")


class CrawlerSettings(BaseSettings):
    """Crawler settings."""

    batch_size: int = Field(50, description="Batch size for processing")
    max_concurrent: int = Field(3, description="Max concurrent requests")
    request_timeout: int = Field(30, description="Request timeout in seconds")

    model_config = SettingsConfigDict(env_prefix="CRAWL_", env_file=str(ENV_FILE), extra="ignore")


class RateLimitSettings(BaseSettings):
    """Rate limiting settings."""

    flood_wait_threshold: int = Field(300, description="FloodWait threshold in seconds")
    max_requests_per_second: float = Field(1.0, description="Max requests per second")

    model_config = SettingsConfigDict(env_prefix="RATELIMIT_", env_file=str(ENV_FILE), extra="ignore")


class SchedulerSettings(BaseSettings):
    """Scheduler settings."""

    discovery_interval_hours: int = Field(1, description="Discovery interval in hours")
    validation_interval_minutes: int = Field(5, description="Validation interval in minutes")
    metadata_interval_minutes: int = Field(5, description="Metadata interval in minutes")
    update_interval_hours: int = Field(6, description="Update interval in hours")

    model_config = SettingsConfigDict(env_prefix="SCHEDULER_", env_file=str(ENV_FILE), extra="ignore")


class APISettings(BaseSettings):
    """API settings."""

    host: str = Field("0.0.0.0", description="API host")
    port: int = Field(8000, description="API port")
    workers: int = Field(1, description="API workers")

    model_config = SettingsConfigDict(env_prefix="API_", env_file=str(ENV_FILE), extra="ignore")


class DashboardSettings(BaseSettings):
    """Dashboard settings."""

    enabled: bool = Field(True, description="Dashboard enabled")
    refresh_seconds: int = Field(30, description="Dashboard refresh interval")

    model_config = SettingsConfigDict(env_prefix="DASHBOARD_", env_file=str(ENV_FILE), extra="ignore")


class Settings(BaseSettings):
    """Main application settings."""

    app_name: str = Field("TGIndex", description="Application name")
    app_version: str = Field("0.1.0", description="Application version")
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Log level")

    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    crawler: CrawlerSettings = Field(default_factory=CrawlerSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    api: APISettings = Field(default_factory=APISettings)
    dashboard: DashboardSettings = Field(default_factory=DashboardSettings)

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
