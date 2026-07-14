"""Razorpay live provider — production, activated once KYC is complete. Stub for Phase 5."""
import logging
from typing import Optional
from app.providers.payment.base import PaymentOrder, PaymentProvider, PaymentVerification

logger = logging.getLogger(__name__)


class RazorpayLiveProvider(PaymentProvider):
    """Razorpay Live Mode — production keys, real money.
    TODO: Implement in Phase 5 alongside razorpay_test (same code, different keys)."""

    async def create_order(self, amount_inr: float, receipt: str, notes: Optional[dict] = None) -> PaymentOrder:
        raise NotImplementedError("Razorpay live provider — implement in Phase 5")

    async def verify_payment(self, order_id: str, payment_id: str, signature: str) -> PaymentVerification:
        raise NotImplementedError("Razorpay live provider — implement in Phase 5")

    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        raise NotImplementedError("Razorpay live provider — implement in Phase 5")
