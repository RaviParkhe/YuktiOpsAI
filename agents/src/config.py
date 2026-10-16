from enum import Enum
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class SeverityLevel(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core App
    APP_NAME: str = "YuktiOps Agent Service"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Database
    # Default to local sqlite for zero-friction local tests; override with postgres in prod/docker
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./yuktiops.db",
        description="Async database connection string (PostgreSQL or SQLite)",
    )

    # Redis / Workers
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for async queues",
    )

    # GitHub App
    GITHUB_APP_ID: Optional[str] = None
    GITHUB_APP_PRIVATE_KEY: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: str = Field(
        default="mock_webhook_secret_for_local_testing",
        description="Webhook secret to verify HMAC SHA256 signatures",
    )

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_ALERT_CHAT_ID: Optional[str] = None

    # LLM Provider
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL_NAME: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # Context & Cost Boundaries
    MAX_DIFF_LINES: int = 1200
    MAX_DIFF_BYTES: int = 60000
    SEVERITY_NOTIFICATION_THRESHOLD: SeverityLevel = SeverityLevel.HIGH


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
