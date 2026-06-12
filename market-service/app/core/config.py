"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "market-service"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://market:market@localhost:5432/market_db",
        description="Async PostgreSQL connection string",
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_quote_ttl_seconds: int = 10

    # Workers
    quote_refresh_interval_seconds: float = 1.0
    news_fetch_interval_seconds: int = 300

    # Market Provider
    market_provider: Literal["mock", "zerodha"] = "mock"
    zerodha_api_key: str | None = None
    zerodha_api_secret: str | None = None
    zerodha_access_token: str | None = None
    zerodha_default_exchange: str = "NSE"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
