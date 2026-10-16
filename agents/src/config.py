from enum import Enum
from functools import lru_cache
from typing import Optional
from pydantic import Field, field_validator
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

    # LLM Provider (Google Gemini)
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash"
    MOCK_LLM_MODE: bool = Field(
        default=False,
        description="When True, LLMService runs in offline deterministic mock mode for CI/evals",
    )

    @property
    def gemini_key(self) -> Optional[str]:
        """Return GEMINI_API_KEY or GOOGLE_API_KEY, whichever is configured."""
        return self.GEMINI_API_KEY or self.GOOGLE_API_KEY

    # Context & Cost Boundaries
    MAX_DIFF_LINES: int = 1200
    MAX_DIFF_BYTES: int = 60000
    SEVERITY_NOTIFICATION_THRESHOLD: SeverityLevel = SeverityLevel.HIGH

    # CORS — comma-separated list of allowed frontend origins.
    # In .env use:  ALLOWED_ORIGINS=http://localhost:3000,https://app.example.com
    # Stored as a plain string; split to list at the CORS middleware call site.
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000",
        description="Comma-separated trusted frontend origins for CORS",
    )

    @property
    def allowed_origins_list(self) -> list:
        """Return ALLOWED_ORIGINS as a split, stripped list of origin strings."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @field_validator("GITHUB_WEBHOOK_SECRET")
    @classmethod
    def validate_webhook_secret_in_production(cls, v: str, info) -> str:
        """Prevent startup in production if the webhook secret is the known public default."""
        # info.data is populated with already-validated fields
        env = info.data.get("ENVIRONMENT", Environment.DEVELOPMENT)
        if env == Environment.PRODUCTION and v == "mock_webhook_secret_for_local_testing":
            raise ValueError(
                "GITHUB_WEBHOOK_SECRET must be overridden in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
