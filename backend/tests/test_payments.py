"""Tests for the payment system — Phase 5.

Tests cover:
- Payment provider factory (correct provider selection)
- OfflineMockPaymentProvider (create_order, verify_payment, verify_webhook)
- Razorpay providers (importability, inheritance)
- Payment model enums and structure
- Subscription model structure
- Payment service function signatures
"""
import hashlib
import hmac
import pytest

# ── Provider Factory Tests ────────────────────────────────────────


def test_payment_provider_factory():
    """get_payment_provider() returns correct provider class."""
    from app.services.payment_service import get_payment_provider
    from app.providers.payment.offline_mock import OfflineMockPaymentProvider

    provider = get_payment_provider()
    # Default PAYMENT_PROVIDER is "offline_mock"
    assert isinstance(provider, OfflineMockPaymentProvider)


def test_payment_provider_factory_imports():
    """All three provider classes can be imported."""
    from app.providers.payment.offline_mock import OfflineMockPaymentProvider
    from app.providers.payment.razorpay_test import RazorpayTestProvider
    from app.providers.payment.razorpay_live import RazorpayLiveProvider

    assert OfflineMockPaymentProvider is not None
    assert RazorpayTestProvider is not None
    assert RazorpayLiveProvider is not None


def test_razorpay_live_inherits_from_test():
    """RazorpayLiveProvider inherits from RazorpayTestProvider."""
    from app.providers.payment.razorpay_test import RazorpayTestProvider
    from app.providers.payment.razorpay_live import RazorpayLiveProvider

    assert issubclass(RazorpayLiveProvider, RazorpayTestProvider)


# ── OfflineMock Provider Tests ────────────────────────────────────


@pytest.mark.asyncio
async def test_offline_mock_create_order():
    """OfflineMock creates orders with mock_order_ prefix."""
    from app.providers.payment.offline_mock import OfflineMockPaymentProvider

    provider = OfflineMockPaymentProvider()
    order = await provider.create_order(amount_inr=99.0, receipt="test_receipt_001")

    assert order.order_id.startswith("mock_order_")
    assert order.amount_inr == 99.0
    assert order.currency == "INR"
    assert order.provider_data["mock"] is True


@pytest.mark.asyncio
async def test_offline_mock_verify_success():
    """OfflineMock verifies payments with correct HMAC signature."""
    from app.providers.payment.offline_mock import (
        OfflineMockPaymentProvider,
        generate_mock_signature,
    )

    provider = OfflineMockPaymentProvider()

    order_id = "mock_order_test123"
    payment_id = "mock_pay_success"
    signature = generate_mock_signature(order_id, payment_id)

    result = await provider.verify_payment(order_id, payment_id, signature)
    assert result.is_valid is True
    assert result.payment_id == payment_id


@pytest.mark.asyncio
async def test_offline_mock_verify_failure():
    """OfflineMock rejects payments with 'fail' in payment_id."""
    from app.providers.payment.offline_mock import OfflineMockPaymentProvider

    provider = OfflineMockPaymentProvider()
    result = await provider.verify_payment(
        "mock_order_test", "mock_pay_fail_xyz", "any_sig"
    )
    assert result.is_valid is False


@pytest.mark.asyncio
async def test_offline_mock_webhook_signature():
    """OfflineMock verifies webhook signatures correctly."""
    from app.providers.payment.offline_mock import (
        OfflineMockPaymentProvider,
        MOCK_WEBHOOK_SECRET,
    )

    provider = OfflineMockPaymentProvider()
    payload = b'{"event": "payment.captured"}'

    # Generate correct signature
    sig = hmac.new(
        MOCK_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()

    assert await provider.verify_webhook_signature(payload, sig) is True
    assert await provider.verify_webhook_signature(payload, "wrong_sig") is False


# ── Payment Model Tests ──────────────────────────────────────────


def test_payment_status_enum():
    """PaymentStatus enum has all expected values."""
    from app.models.payment import PaymentStatus

    assert PaymentStatus.PENDING == "pending"
    assert PaymentStatus.SUCCESS == "success"
    assert PaymentStatus.FAILED == "failed"
    assert PaymentStatus.REFUNDED == "refunded"
    assert len(PaymentStatus) == 4


def test_payment_provider_enum():
    """PaymentProviderEnum has all expected values."""
    from app.models.payment import PaymentProviderEnum

    assert PaymentProviderEnum.OFFLINE_MOCK == "offline_mock"
    assert PaymentProviderEnum.RAZORPAY_TEST == "razorpay_test"
    assert PaymentProviderEnum.RAZORPAY_LIVE == "razorpay_live"
    assert len(PaymentProviderEnum) == 3


def test_subscription_status_enum():
    """SubscriptionStatus enum has all expected values."""
    from app.models.payment import SubscriptionStatus

    assert SubscriptionStatus.ACTIVE == "active"
    assert SubscriptionStatus.EXPIRED == "expired"
    assert SubscriptionStatus.CANCELLED == "cancelled"
    assert SubscriptionStatus.TRIAL == "trial"


def test_subscription_model_structure():
    """Subscription model has expected columns."""
    from app.models.payment import Subscription

    mapper = Subscription.__table__
    col_names = {c.name for c in mapper.columns}

    expected = {"id", "name", "description", "price_inr", "duration_days", "features", "is_active"}
    assert expected.issubset(col_names), f"Missing columns: {expected - col_names}"


def test_payment_model_structure():
    """Payment model has expected columns."""
    from app.models.payment import Payment

    mapper = Payment.__table__
    col_names = {c.name for c in mapper.columns}

    expected = {
        "id", "user_id", "subscription_id", "amount_inr", "currency",
        "status", "provider", "provider_order_id", "provider_payment_id",
        "provider_signature", "metadata_json", "paid_at", "expires_at",
    }
    assert expected.issubset(col_names), f"Missing columns: {expected - col_names}"


# ── Payment Service Tests ─────────────────────────────────────────


def test_payment_service_importable():
    """All payment service functions can be imported."""
    from app.services.payment_service import (
        get_payment_provider,
        get_subscription_plans,
        create_payment_order,
        verify_and_activate,
        handle_webhook,
        get_user_subscription,
        check_subscription_active,
        get_payment_history,
    )

    assert callable(get_payment_provider)
    assert callable(get_subscription_plans)
    assert callable(create_payment_order)
    assert callable(verify_and_activate)
    assert callable(handle_webhook)
    assert callable(get_user_subscription)
    assert callable(check_subscription_active)
    assert callable(get_payment_history)


# ── Payment Schema Tests ─────────────────────────────────────────


def test_payment_schemas_importable():
    """All payment schemas can be imported."""
    from app.schemas.payment import (
        SubscriptionPlanResponse,
        PaymentOrderRequest,
        PaymentOrderResponse,
        PaymentVerifyRequest,
        PaymentVerifyResponse,
        RazorpayWebhookEvent,
        PaymentHistoryItem,
        PaymentHistoryResponse,
        UserSubscriptionResponse,
    )

    assert SubscriptionPlanResponse is not None
    assert PaymentOrderRequest is not None


def test_payment_order_request_schema():
    """PaymentOrderRequest validates correctly."""
    from app.schemas.payment import PaymentOrderRequest

    req = PaymentOrderRequest(subscription_id="test-uuid-123")
    assert req.subscription_id == "test-uuid-123"
    assert req.notes is None


def test_payment_verify_request_schema():
    """PaymentVerifyRequest validates correctly."""
    from app.schemas.payment import PaymentVerifyRequest

    req = PaymentVerifyRequest(
        order_id="order_123",
        payment_id="pay_456",
        signature="sig_789",
    )
    assert req.order_id == "order_123"
    assert req.payment_id == "pay_456"
    assert req.signature == "sig_789"


# ── Payment Router Tests ─────────────────────────────────────────


def test_payment_router_importable():
    """Payment router can be imported and has expected routes."""
    from app.routers.payments import router

    routes = [r.path for r in router.routes]
    assert "/plans" in routes
    assert "/create-order" in routes
    assert "/verify" in routes
    assert "/webhook" in routes
    assert "/subscription" in routes
    assert "/history" in routes


def test_payment_router_has_correct_endpoint_count():
    """Payment router has exactly 6 endpoints."""
    from app.routers.payments import router

    # Count only API routes (exclude internal fastapi routes)
    api_routes = [r for r in router.routes if hasattr(r, 'methods')]
    assert len(api_routes) == 6, f"Expected 6 endpoints, got {len(api_routes)}"


# ── Seed Script Tests ─────────────────────────────────────────────


def test_seed_subscriptions_importable():
    """Subscription seed script can be imported."""
    from app.scripts.seed_subscriptions import PLANS, seed_subscriptions

    assert len(PLANS) == 4
    assert PLANS[0]["name"] == "Free Trial"
    assert PLANS[0]["price_inr"] == 0.00
    assert PLANS[1]["name"] == "Monthly"
    assert PLANS[1]["price_inr"] == 99.00
    assert PLANS[2]["name"] == "Quarterly"
    assert PLANS[2]["price_inr"] == 249.00
    assert PLANS[3]["name"] == "Annual"
    assert PLANS[3]["price_inr"] == 799.00
