"""Razorpay test mode provider — uses real Razorpay sandbox API.
Uses test keys from .env (no KYC required). Stub for Phase 5."""
import logging
from typing import Optional
from app.providers.payment.base import PaymentOrder, PaymentProvider, PaymentVerification

logger = logging.getLogger(__name__)


class RazorpayTestProvider(PaymentProvider):
    """Razorpay Test Mode — real sandbox API, test UPI IDs like success@razorpay.
    TODO: Implement in Phase 5."""

    async def create_order(self, amount_inr: float, receipt: str, notes: Optional[dict] = None) -> PaymentOrder:
        raise NotImplementedError("Razorpay test provider — implement in Phase 5")

    async def verify_payment(self, order_id: str, payment_id: str, signature: str) -> PaymentVerification:
        raise NotImplementedError("Razorpay test provider — implement in Phase 5")

    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        raise NotImplementedError("Razorpay test provider — implement in Phase 5")
