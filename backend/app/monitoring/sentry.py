"""Sentry integration — error tracking and performance monitoring.

Free tier: 5K errors/month, 1M transactions — generous at pilot scale.

Usage:
    import sentry_sdk at app startup to auto-instrument FastAPI.
    Set SENTRY_DSN in .env to enable (leave blank to disable).
"""
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


def init_sentry() -> bool:
    """Initialize Sentry SDK if SENTRY_DSN is configured.

    Returns True if initialized, False if skipped.

    Must be called BEFORE FastAPI app is created, typically
    at the top of app/main.py.
    """
    sentry_dsn = getattr(settings, "SENTRY_DSN", "")

    if not sentry_dsn:
        logger.info("[SENTRY] No SENTRY_DSN configured — error tracking disabled")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=settings.ENVIRONMENT,
            release=f"vidyamitra@{getattr(settings, 'APP_VERSION', '0.1.0')}",

            # Performance monitoring
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,

            # Send all errors in pilot, sample in production
            profiles_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,

            # Integrations
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                RedisIntegration(),
                LoggingIntegration(
                    level=logging.WARNING,
                    event_level=logging.ERROR,
                ),
            ],

            # Filter out health check transactions
            before_send_transaction=_filter_health_checks,

            # Don't send PII (DPDP Act compliance)
            send_default_pii=False,

            # Add custom tags
            _experiments={
                "profiles_sample_rate": 0.1,
            },
        )

        # Set common tags
        sentry_sdk.set_tag("platform", "vidyamitra")
        sentry_sdk.set_tag("environment", settings.ENVIRONMENT)

        logger.info(f"[SENTRY] Initialized for {settings.ENVIRONMENT} environment")
        return True

    except ImportError:
        logger.info("[SENTRY] sentry-sdk not installed — pip install sentry-sdk[fastapi]")
        return False
    except Exception as e:
        logger.error(f"[SENTRY] Failed to initialize: {e}")
        return False


def _filter_health_checks(event: dict, hint: dict) -> Optional[dict]:
    """Filter out health check transactions to save quota."""
    transaction = event.get("transaction", "")
    if "/health" in transaction:
        return None
    return event


def capture_message(message: str, level: str = "info", extras: Optional[dict] = None):
    """Convenience wrapper to send a Sentry message."""
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            if extras:
                for key, value in extras.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)
    except ImportError:
        pass


def capture_exception(exception: Exception, extras: Optional[dict] = None):
    """Convenience wrapper to send a Sentry exception."""
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            if extras:
                for key, value in extras.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(exception)
    except ImportError:
        pass
