"""Razorpay live provider — production, activated once KYC is complete.

Per ARCHITECTURE.md §10: same code path as razorpay_test, different keys.
The PaymentProvider factory in payment_service.py selects this based on
PAYMENT_PROVIDER=razorpay_live in .env.

IMPORTANT: This uses REAL money. Double-check RAZORPAY_KEY_ID and
RAZORPAY_KEY_SECRET are production keys before enabling.
"""
import logging

from app.providers.payment.razorpay_test import RazorpayTestProvider

logger = logging.getLogger(__name__)


class RazorpayLiveProvider(RazorpayTestProvider):
    """Razorpay Live Mode — production keys, real money.

    Inherits all logic from RazorpayTestProvider (same API, same SDK).
    The only differences:
    1. Uses production API keys (set RAZORPAY_KEY_ID/SECRET to live keys)
    2. Stricter logging (no debug data in logs)
    3. Webhook secret must be the production webhook secret
    """

    def __init__(self) -> None:
        super().__init__()
        # Validate that keys look like live keys (start with "rzp_live_")
        if self.key_id and not self.key_id.startswith("rzp_live_"):
            logger.warning(
                "[RAZORPAY LIVE] RAZORPAY_KEY_ID does not start with 'rzp_live_' — "
                "are you sure you're using production keys?"
            )
        if not self.webhook_secret:
            logger.error(
                "[RAZORPAY LIVE] RAZORPAY_WEBHOOK_SECRET is required in production — "
                "unsigned webhooks will be rejected"
            )
        logger.info("[RAZORPAY LIVE] Production payment provider initialized")
