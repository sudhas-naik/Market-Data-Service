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

    # Firebase Authentication
    firebase_auth_enabled: bool = True
    firebase_project_id: str | None = None
    firebase_credentials_path: str | None = None
    firebase_credentials_json: str | None = None
    # Individual service account fields (alternative to JSON file)
    firebase_private_key_id: str | None = None
    firebase_private_key: str | None = None
    firebase_client_email: str | None = None
    firebase_client_id: str | None = None
    firebase_client_x509_cert_url: str | None = None
    # Dev only: allow X-User-ID header when Firebase auth is disabled
    firebase_auth_dev_bypass: bool = False

    def has_firebase_env_credentials(self) -> bool:
        """Return True when required Firebase fields are set in environment."""
        return bool(
            self.firebase_project_id
            and self.firebase_private_key
            and self.firebase_client_email
        )

    # Market Provider
    zerodha_api_key: str | None = None
    zerodha_api_secret: str | None = None
    zerodha_access_token: str | None = None
    zerodha_request_token: str | None = None
    zerodha_default_exchange: str = "NSE"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
