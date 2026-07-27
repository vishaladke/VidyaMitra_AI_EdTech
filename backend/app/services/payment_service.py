"""Payment service — full payment flow orchestration.

Handles the complete lifecycle:
1. List subscription plans
2. Create payment order (via provider)
3. Verify payment callback
4. Handle webhooks (payment.captured, payment.failed, refund.processed)
5. Manage user subscriptions
6. Payment history

Per ARCHITECTURE.md §10: PaymentProvider interface with three implementations,
selected by PAYMENT_PROVIDER env var — same code path with one config change.
"""
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.payment import (
    Payment,
    PaymentProviderEnum,
    PaymentStatus,
    Subscription,
    SubscriptionStatus,
)
from app.models.user import User
from app.providers.payment.base import PaymentProvider
from app.providers.payment.offline_mock import OfflineMockPaymentProvider
from app.providers.payment.razorpay_test import RazorpayTestProvider
from app.providers.payment.razorpay_live import RazorpayLiveProvider

logger = logging.getLogger(__name__)


# ── Provider Factory ──────────────────────────────────────────────

def get_payment_provider() -> PaymentProvider:
    """Factory: select payment provider based on PAYMENT_PROVIDER env var."""
    providers = {
        "offline_mock": OfflineMockPaymentProvider,
        "razorpay_test": RazorpayTestProvider,
        "razorpay_live": RazorpayLiveProvider,
    }
    provider_class = providers.get(settings.PAYMENT_PROVIDER, OfflineMockPaymentProvider)
    return provider_class()


# ── Subscription Plans ────────────────────────────────────────────

async def get_subscription_plans(db: AsyncSession) -> list[dict]:
    """List all active subscription plans."""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.is_active == True)
        .order_by(Subscription.price_inr.asc())
    )
    plans = result.scalars().all()

    return [
        {
            "id": str(plan.id),
            "name": plan.name,
            "description": plan.description,
            "price_inr": float(plan.price_inr),
            "duration_days": plan.duration_days,
            "features": plan.features,
            "is_active": plan.is_active,
        }
        for plan in plans
    ]


# ── Payment Order Creation ────────────────────────────────────────

async def create_payment_order(
    db: AsyncSession,
    user_id: uuid.UUID,
    subscription_id: uuid.UUID,
    notes: Optional[dict] = None,
) -> dict:
    """Create a payment order: persist Payment record + create provider order.

    Returns dict with order details for the frontend to launch checkout.
    """
    # Fetch the subscription plan
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.is_active == True,
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise ValueError("Subscription plan not found or inactive")

    # Create provider order
    provider = get_payment_provider()
    receipt = f"sub_{str(user_id)[:8]}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    order = await provider.create_order(
        amount_inr=float(plan.price_inr),
        receipt=receipt,
        notes={**(notes or {}), "user_id": str(user_id), "plan": plan.name},
    )

    # Map provider name to enum
    provider_enum = {
        "offline_mock": PaymentProviderEnum.OFFLINE_MOCK,
        "razorpay_test": PaymentProviderEnum.RAZORPAY_TEST,
        "razorpay_live": PaymentProviderEnum.RAZORPAY_LIVE,
    }.get(settings.PAYMENT_PROVIDER, PaymentProviderEnum.OFFLINE_MOCK)

    # Persist payment record
    payment = Payment(
        user_id=user_id,
        subscription_id=subscription_id,
        amount_inr=float(plan.price_inr),
        currency="INR",
        status=PaymentStatus.PENDING,
        provider=provider_enum,
        provider_order_id=order.order_id,
        metadata_json={"receipt": receipt, "plan_name": plan.name},
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    logger.info(f"💳 Payment order created: {payment.id} for user {user_id}, plan {plan.name}")

    return {
        "order_id": order.order_id,
        "payment_id": str(payment.id),
        "amount_inr": float(plan.price_inr),
        "currency": "INR",
        "provider": settings.PAYMENT_PROVIDER,
        "provider_data": order.provider_data,
        "plan": {
            "name": plan.name,
            "duration_days": plan.duration_days,
        },
    }


# ── Payment Verification ─────────────────────────────────────────

async def verify_and_activate(
    db: AsyncSession,
    order_id: str,
    payment_id: str,
    signature: str,
) -> dict:
    """Verify payment callback and activate subscription if valid.

    Called after the client-side Razorpay checkout completes.
    """
    # Find our payment record by provider order ID
    result = await db.execute(
        select(Payment).where(Payment.provider_order_id == order_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        logger.warning(f"⚠️ Payment verification: no record for order {order_id}")
        return {"success": False, "message": "Payment record not found"}

    if payment.status == PaymentStatus.SUCCESS:
        return {"success": True, "message": "Payment already verified"}

    # Verify with provider
    provider = get_payment_provider()
    verification = await provider.verify_payment(order_id, payment_id, signature)

    if verification.is_valid:
        # Update payment record
        payment.status = PaymentStatus.SUCCESS
        payment.provider_payment_id = payment_id
        payment.provider_signature = signature
        payment.paid_at = datetime.now(timezone.utc)

        # Calculate expiry from subscription plan
        if payment.subscription_id:
            plan_result = await db.execute(
                select(Subscription).where(Subscription.id == payment.subscription_id)
            )
            plan = plan_result.scalar_one_or_none()
            if plan:
                payment.expires_at = datetime.now(timezone.utc) + timedelta(days=plan.duration_days)

        await db.commit()
        logger.info(f"✅ Payment verified and activated: {payment.id}")

        return {
            "success": True,
            "message": "Payment verified successfully",
            "subscription_status": "active",
            "expires_at": payment.expires_at.isoformat() if payment.expires_at else None,
        }
    else:
        payment.status = PaymentStatus.FAILED
        payment.metadata_json = {
            **(payment.metadata_json or {}),
            "verification_error": verification.error,
        }
        await db.commit()

        logger.warning(f"❌ Payment verification failed: {payment.id} — {verification.error}")

        return {
            "success": False,
            "message": f"Payment verification failed: {verification.error}",
        }


# ── Webhook Processing ───────────────────────────────────────────

async def handle_webhook(
    db: AsyncSession,
    payload: bytes,
    signature: str,
    event_data: dict,
) -> dict:
    """Process Razorpay webhook events.

    Events handled:
    - payment.captured → mark SUCCESS, activate subscription
    - payment.failed → mark FAILED
    - refund.processed → mark REFUNDED
    """
    # Verify webhook signature first
    provider = get_payment_provider()
    if not await provider.verify_webhook_signature(payload, signature):
        logger.warning("🚫 Webhook signature verification failed — rejecting")
        return {"status": "rejected", "reason": "invalid_signature"}

    event_type = event_data.get("event", "")
    payment_entity = (
        event_data.get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )

    order_id = payment_entity.get("order_id", "")
    rpay_payment_id = payment_entity.get("id", "")

    logger.info(f"📨 Webhook received: {event_type} order={order_id} payment={rpay_payment_id}")

    # Find our payment record
    result = await db.execute(
        select(Payment).where(Payment.provider_order_id == order_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        logger.warning(f"⚠️ Webhook: no payment record for order {order_id}")
        return {"status": "ignored", "reason": "no_matching_record"}

    if event_type == "payment.captured":
        if payment.status != PaymentStatus.SUCCESS:
            payment.status = PaymentStatus.SUCCESS
            payment.provider_payment_id = rpay_payment_id
            payment.paid_at = datetime.now(timezone.utc)

            # Set expiry
            if payment.subscription_id:
                plan_result = await db.execute(
                    select(Subscription).where(Subscription.id == payment.subscription_id)
                )
                plan = plan_result.scalar_one_or_none()
                if plan:
                    payment.expires_at = datetime.now(timezone.utc) + timedelta(days=plan.duration_days)

            await db.commit()
            logger.info(f"✅ Webhook: payment captured — {payment.id}")

    elif event_type == "payment.failed":
        if payment.status == PaymentStatus.PENDING:
            payment.status = PaymentStatus.FAILED
            payment.metadata_json = {
                **(payment.metadata_json or {}),
                "failure_reason": payment_entity.get("error_description", "Unknown"),
            }
            await db.commit()
            logger.info(f"❌ Webhook: payment failed — {payment.id}")

    elif event_type == "refund.processed":
        payment.status = PaymentStatus.REFUNDED
        payment.metadata_json = {
            **(payment.metadata_json or {}),
            "refund_id": event_data.get("payload", {}).get("refund", {}).get("entity", {}).get("id"),
        }
        # Void the subscription expiry
        payment.expires_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"💸 Webhook: refund processed — {payment.id}")

    else:
        logger.info(f"ℹ️ Webhook: unhandled event type — {event_type}")
        return {"status": "ignored", "reason": f"unhandled_event: {event_type}"}

    return {"status": "processed", "event": event_type}


# ── User Subscription Status ─────────────────────────────────────

async def get_user_subscription(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Get the current active subscription for a user."""
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Payment, Subscription)
        .outerjoin(Subscription, Payment.subscription_id == Subscription.id)
        .where(
            and_(
                Payment.user_id == user_id,
                Payment.status == PaymentStatus.SUCCESS,
                Payment.expires_at > now,
            )
        )
        .order_by(Payment.expires_at.desc())
        .limit(1)
    )
    row = result.one_or_none()

    if not row:
        return {
            "has_active_subscription": False,
            "plan_name": None,
            "status": None,
            "expires_at": None,
            "days_remaining": None,
            "features": None,
        }

    payment, plan = row
    days_remaining = (payment.expires_at - now).days if payment.expires_at else 0

    return {
        "has_active_subscription": True,
        "plan_name": plan.name if plan else "Unknown",
        "status": "active",
        "expires_at": payment.expires_at.isoformat() if payment.expires_at else None,
        "days_remaining": max(0, days_remaining),
        "features": plan.features if plan else None,
    }


async def check_subscription_active(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """Quick boolean check: does this user have an active subscription?"""
    now = datetime.now(timezone.utc)

    count = await db.scalar(
        select(func.count())
        .select_from(Payment)
        .where(
            and_(
                Payment.user_id == user_id,
                Payment.status == PaymentStatus.SUCCESS,
                Payment.expires_at > now,
            )
        )
    )
    return (count or 0) > 0


# ── Payment History ───────────────────────────────────────────────

async def get_payment_history(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Paginated payment history for a user."""
    # Count total
    total = await db.scalar(
        select(func.count())
        .select_from(Payment)
        .where(Payment.user_id == user_id)
    )

    # Fetch page
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Payment, Subscription)
        .outerjoin(Subscription, Payment.subscription_id == Subscription.id)
        .where(Payment.user_id == user_id)
        .order_by(Payment.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = result.all()

    payments = []
    for payment, plan in rows:
        payments.append({
            "id": str(payment.id),
            "amount_inr": float(payment.amount_inr),
            "currency": payment.currency,
            "status": payment.status.value,
            "provider": payment.provider.value,
            "subscription_name": plan.name if plan else None,
            "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
            "created_at": payment.created_at.isoformat(),
        })

    return {"payments": payments, "total": total or 0}
