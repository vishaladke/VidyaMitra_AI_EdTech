"""Abstract PaymentProvider interface.

Per ARCHITECTURE.md §10: A PaymentProvider interface with three implementations,
selected by an environment variable — same code path with one config change.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class PaymentOrder:
    """Represents a created payment order."""
    order_id: str
    amount_inr: float
    currency: str = "INR"
    provider_data: Optional[dict] = None


@dataclass
class PaymentVerification:
    """Result of payment verification."""
    is_valid: bool
    payment_id: Optional[str] = None
    order_id: Optional[str] = None
    signature: Optional[str] = None
    error: Optional[str] = None


class PaymentProvider(ABC):
    """Interface for payment providers (offline_mock, razorpay_test, razorpay_live)."""

    @abstractmethod
    async def create_order(self, amount_inr: float, receipt: str, notes: Optional[dict] = None) -> PaymentOrder:
        """Create a payment order."""
        ...

    @abstractmethod
    async def verify_payment(self, order_id: str, payment_id: str, signature: str) -> PaymentVerification:
        """Verify a payment after callback."""
        ...

    @abstractmethod
    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook callback signature — MUST stay on regardless of mode.
        Per DEPLOYMENT.md: don't trust unsigned callbacks."""
        ...
