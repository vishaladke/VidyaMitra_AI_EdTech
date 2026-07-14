"""Offline mock payment provider — pure local, zero network calls.

Per ARCHITECTURE.md §10: `offline_mock` — for fully offline dev.
"""
import hashlib
import hmac
import uuid
from typing import Optional

from app.providers.payment.base import PaymentOrder, PaymentProvider, PaymentVerification

# Fixed mock webhook secret for local testing
MOCK_WEBHOOK_SECRET = "mock_webhook_secret_for_local_dev"


class OfflineMockPaymentProvider(PaymentProvider):
    """Pure local mock — no network calls, deterministic behavior.
    
    Test UPI IDs (mirroring Razorpay's convention):
    - "success@mock" → payment succeeds
    - "failure@mock" → payment fails
    """

    async def create_order(self, amount_inr: float, receipt: str, notes: Optional[dict] = None) -> PaymentOrder:
        order_id = f"mock_order_{uuid.uuid4().hex[:12]}"
        return PaymentOrder(
            order_id=order_id,
            amount_inr=amount_inr,
            currency="INR",
            provider_data={"mock": True, "receipt": receipt, "notes": notes},
        )

    async def verify_payment(self, order_id: str, payment_id: str, signature: str) -> PaymentVerification:
        # Simulate: any payment_id containing "fail" is a failure
        if "fail" in payment_id.lower():
            return PaymentVerification(
                is_valid=False,
                payment_id=payment_id,
                order_id=order_id,
                error="Simulated payment failure",
            )

        # Verify the mock signature
        expected = hmac.new(
            MOCK_WEBHOOK_SECRET.encode(),
            f"{order_id}|{payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()

        return PaymentVerification(
            is_valid=(signature == expected),
            payment_id=payment_id,
            order_id=order_id,
            signature=signature,
        )

    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Even the mock verifies signatures — habit, not just correctness."""
        expected = hmac.new(
            MOCK_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


def generate_mock_signature(order_id: str, payment_id: str) -> str:
    """Helper for tests: generate the expected mock signature."""
    return hmac.new(
        MOCK_WEBHOOK_SECRET.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
