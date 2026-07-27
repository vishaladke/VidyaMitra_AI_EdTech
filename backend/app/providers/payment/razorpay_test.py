"""Razorpay test mode provider — uses real Razorpay sandbox API.

Uses test keys from .env (no KYC required).
Test UPI IDs: success@razorpay, failure@razorpay

Per ARCHITECTURE.md §10: same code path with one config change.
"""
import hashlib
import hmac
import json
import logging
from typing import Optional

import httpx

from app.config import settings
from app.providers.payment.base import PaymentOrder, PaymentProvider, PaymentVerification

logger = logging.getLogger(__name__)

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"


class RazorpayTestProvider(PaymentProvider):
    """Razorpay Test Mode — real sandbox API, test UPI IDs like success@razorpay.

    Uses RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET from environment.
    In test mode, no real money is charged.
    """

    def __init__(self) -> None:
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

        if not self.key_id or not self.key_secret:
            logger.warning(
                "[RAZORPAY TEST] RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET not set — "
                "API calls will fail. Set them in .env for sandbox testing."
            )

    @property
    def _auth(self) -> tuple[str, str]:
        """HTTP Basic Auth credentials for Razorpay API."""
        return (self.key_id, self.key_secret)

    async def create_order(
        self, amount_inr: float, receipt: str, notes: Optional[dict] = None
    ) -> PaymentOrder:
        """Create a Razorpay order.

        Razorpay expects amount in paise (1 INR = 100 paise).
        """
        amount_paise = int(round(amount_inr * 100))

        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,  # Auto-capture on payment success
        }
        if notes:
            payload["notes"] = notes

        logger.info(f"[RAZORPAY TEST] Creating order: ₹{amount_inr} receipt={receipt}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RAZORPAY_API_BASE}/orders",
                json=payload,
                auth=self._auth,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"[RAZORPAY TEST] Order creation failed: {error_detail}")
                raise RuntimeError(f"Razorpay order creation failed: {error_detail}")

            order_data = response.json()

        logger.info(f"[RAZORPAY TEST] Order created: {order_data['id']}")

        return PaymentOrder(
            order_id=order_data["id"],
            amount_inr=amount_inr,
            currency="INR",
            provider_data={
                "razorpay_order_id": order_data["id"],
                "razorpay_key_id": self.key_id,
                "amount_paise": amount_paise,
                "status": order_data.get("status"),
            },
        )

    async def verify_payment(
        self, order_id: str, payment_id: str, signature: str
    ) -> PaymentVerification:
        """Verify payment signature after client-side checkout callback.

        Razorpay signs: order_id|payment_id with the key_secret.
        """
        try:
            expected_signature = hmac.new(
                self.key_secret.encode("utf-8"),
                f"{order_id}|{payment_id}".encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            is_valid = hmac.compare_digest(expected_signature, signature)

            if is_valid:
                logger.info(f"[RAZORPAY TEST] Payment verified: {payment_id}")
            else:
                logger.warning(
                    f"[RAZORPAY TEST] Payment verification failed: {payment_id} — signature mismatch"
                )

            return PaymentVerification(
                is_valid=is_valid,
                payment_id=payment_id,
                order_id=order_id,
                signature=signature,
                error=None if is_valid else "Signature verification failed",
            )

        except Exception as e:
            logger.error(f"[RAZORPAY TEST] Payment verification error: {e}")
            return PaymentVerification(
                is_valid=False,
                payment_id=payment_id,
                order_id=order_id,
                error=str(e),
            )

    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Razorpay webhook callback signature.

        Per DEPLOYMENT.md: don't trust unsigned callbacks.
        Razorpay signs the raw request body with the webhook secret.
        """
        if not self.webhook_secret:
            logger.error("[RAZORPAY TEST] RAZORPAY_WEBHOOK_SECRET not set — rejecting webhook")
            return False

        try:
            expected = hmac.new(
                self.webhook_secret.encode("utf-8"),
                payload,
                hashlib.sha256,
            ).hexdigest()

            is_valid = hmac.compare_digest(expected, signature)

            if not is_valid:
                logger.warning("[RAZORPAY TEST] Webhook signature mismatch — rejecting")

            return is_valid

        except Exception as e:
            logger.error(f"[RAZORPAY TEST] Webhook signature verification error: {e}")
            return False

    async def fetch_payment_details(self, payment_id: str) -> Optional[dict]:
        """Fetch payment details from Razorpay API (for reconciliation)."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{RAZORPAY_API_BASE}/payments/{payment_id}",
                    auth=self._auth,
                    timeout=30.0,
                )
                if response.status_code == 200:
                    return response.json()
                logger.warning(f"[RAZORPAY TEST] Failed to fetch payment {payment_id}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"[RAZORPAY TEST] Error fetching payment {payment_id}: {e}")
            return None
