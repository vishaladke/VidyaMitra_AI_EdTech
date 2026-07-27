"""Payment and subscription schemas — Pydantic request/response models."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Subscription Plans ────────────────────────────────────────────

class SubscriptionPlanResponse(BaseModel):
    """A subscription plan available for purchase."""
    id: str
    name: str
    description: Optional[str] = None
    price_inr: float
    duration_days: int
    features: Optional[dict] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class SubscriptionPlanListResponse(BaseModel):
    plans: list[SubscriptionPlanResponse]
    total: int


# ── Payment Order ─────────────────────────────────────────────────

class PaymentOrderRequest(BaseModel):
    """Request to create a new payment order."""
    subscription_id: str = Field(..., description="UUID of the subscription plan")
    notes: Optional[dict] = Field(None, description="Optional metadata")


class PaymentOrderResponse(BaseModel):
    """Response after creating a payment order."""
    order_id: str
    payment_id: str  # Our internal payment record ID
    amount_inr: float
    currency: str = "INR"
    provider: str
    provider_data: Optional[dict] = None  # Contains razorpay_key_id for checkout


# ── Payment Verification ─────────────────────────────────────────

class PaymentVerifyRequest(BaseModel):
    """Client sends this after Razorpay checkout callback."""
    order_id: str = Field(..., description="Razorpay order ID (or mock order ID)")
    payment_id: str = Field(..., description="Razorpay payment ID")
    signature: str = Field(..., description="Razorpay signature for verification")


class PaymentVerifyResponse(BaseModel):
    """Result of payment verification."""
    success: bool
    message: str
    subscription_status: Optional[str] = None
    expires_at: Optional[str] = None


# ── Webhook ───────────────────────────────────────────────────────

class RazorpayWebhookEvent(BaseModel):
    """Razorpay webhook event payload structure."""
    entity: str = "event"
    account_id: Optional[str] = None
    event: str  # e.g., "payment.captured", "payment.failed", "refund.processed"
    contains: Optional[list[str]] = None
    payload: dict

    class Config:
        extra = "allow"  # Razorpay may add fields


# ── Payment History ───────────────────────────────────────────────

class PaymentHistoryItem(BaseModel):
    """A single payment record in the user's history."""
    id: str
    amount_inr: float
    currency: str = "INR"
    status: str
    provider: str
    subscription_name: Optional[str] = None
    paid_at: Optional[str] = None
    created_at: str


class PaymentHistoryResponse(BaseModel):
    """Paginated payment history."""
    payments: list[PaymentHistoryItem]
    total: int


# ── User Subscription ────────────────────────────────────────────

class UserSubscriptionResponse(BaseModel):
    """Current subscription status for a user."""
    has_active_subscription: bool
    plan_name: Optional[str] = None
    status: Optional[str] = None
    expires_at: Optional[str] = None
    days_remaining: Optional[int] = None
    features: Optional[dict] = None
