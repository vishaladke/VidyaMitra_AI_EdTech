"""Application settings from environment variables using pydantic-settings."""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """All configuration is loaded from environment variables.
    Secrets never live in code."""

    # ── Core ──────────────────────────────────────────────
    ENVIRONMENT: Literal["local", "pilot", "production"] = "local"
    JWT_SECRET: str = "change_me_to_a_long_random_string"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SUPERADMIN_URL_PATH: str = "change-me-to-something-unguessable"

    # ── Database ──────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://edtech:edtech_local_dev@postgres:5432/edtech_platform"

    # ── Cache ─────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Object Storage (Cloudflare R2) ────────────────────
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "edtech-media"

    # ── AI — Anthropic ────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    AI_DEFAULT_MODEL: str = "claude-haiku-4-5-20251001"
    AI_ESCALATION_MODEL: str = "claude-sonnet-4-6"

    # ── AI — Embeddings (for pgvector semantic cache) ─────
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

    # ── Voice — Sarvam AI ─────────────────────────────────
    SARVAM_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""

    # ── OTP ───────────────────────────────────────────────
    OTP_PROVIDER: Literal["firebase", "msg91", "dev_mock"] = "dev_mock"
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    MSG91_AUTH_KEY: str = ""
    DEV_OTP_CODE: str = "123456"  # Fixed OTP for local dev — never used in production

    # ── Payments ──────────────────────────────────────────
    PAYMENT_PROVIDER: Literal["offline_mock", "razorpay_test", "razorpay_live"] = "offline_mock"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # ── WhatsApp ──────────────────────────────────────────
    WHATSAPP_BSP_API_KEY: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = ""

    # ── Realtime Gateway ──────────────────────────────────
    BACKEND_URL: str = "http://backend:8000"

    # ── Rate Limiting ─────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_SUPERADMIN_LOGIN_ATTEMPTS: int = 5
    RATE_LIMIT_SUPERADMIN_LOCKOUT_MINUTES: int = 15

    # ── CORS ──────────────────────────────────────────────
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:5173", "http://localhost:4000"])

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()
