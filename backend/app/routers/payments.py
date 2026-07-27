"""Payment router — subscription plans, order creation, verification, webhooks.

Endpoints:
- GET  /api/payments/plans          — list subscription plans (public)
- POST /api/payments/create-order   — create payment order (auth required)
- POST /api/payments/verify         — verify after checkout callback
- POST /api/payments/webhook        — Razorpay webhook (no auth, sig verified)
- GET  /api/payments/subscription   — current subscription status
- GET  /api/payments/history        — payment history
"""
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.payment import (
    PaymentOrderRequest,
    PaymentOrderResponse,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
)
from app.services.payment_service import (
    get_subscription_plans,
    create_payment_order,
    verify_and_activate,
    handle_webhook,
    get_user_subscription,
    get_payment_history,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["payments"])


# ── Subscription Plans (Public) ───────────────────────────────────

@router.get("/plans")
async def list_plans(db: AsyncSession = Depends(get_db)):
    """List all active subscription plans. No auth required."""
    plans = await get_subscription_plans(db)
    return {"plans": plans, "total": len(plans)}


# ── Create Order ──────────────────────────────────────────────────

@router.post("/create-order")
async def create_order(
    body: PaymentOrderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a payment order. Returns details for launching Razorpay checkout."""
    try:
        subscription_uuid = uuid.UUID(body.subscription_id)
    except ValueError:
        raise HTTPException(400, "Invalid subscription_id format")

    try:
        result = await create_payment_order(
            db=db,
            user_id=user.id,
            subscription_id=subscription_uuid,
            notes=body.notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(502, f"Payment provider error: {e}")


# ── Verify Payment ───────────────────────────────────────────────

@router.post("/verify")
async def verify_payment(
    body: PaymentVerifyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify payment after client-side checkout callback.

    The frontend sends this after Razorpay checkout completes.
    """
    result = await verify_and_activate(
        db=db,
        order_id=body.order_id,
        payment_id=body.payment_id,
        signature=body.signature,
    )
    if not result.get("success"):
        raise HTTPException(400, result.get("message", "Verification failed"))
    return result


# ── Razorpay Webhook ─────────────────────────────────────────────

@router.post("/webhook")
async def payment_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive Razorpay webhook events.

    No JWT auth — webhook signature is verified instead.
    Per DEPLOYMENT.md: don't trust unsigned callbacks.
    """
    payload = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    try:
        event_data = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON payload")

    result = await handle_webhook(
        db=db,
        payload=payload,
        signature=signature,
        event_data=event_data,
    )

    if result.get("status") == "rejected":
        raise HTTPException(401, "Invalid webhook signature")

    return result


# ── Subscription Status ──────────────────────────────────────────

@router.get("/subscription")
async def subscription_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current subscription status for the authenticated user."""
    return await get_user_subscription(db, user.id)


# ── Payment History ───────────────────────────────────────────────

@router.get("/history")
async def payment_history(
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Paginated payment history for the authenticated user."""
    return await get_payment_history(db, user.id, page, page_size)
