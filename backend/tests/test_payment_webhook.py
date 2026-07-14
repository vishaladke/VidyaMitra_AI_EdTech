"""Payment webhook signature verification tests — expensive-bug path."""
import hashlib
import hmac

import pytest

from app.providers.payment.offline_mock import (
    MOCK_WEBHOOK_SECRET,
    OfflineMockPaymentProvider,
    generate_mock_signature,
)


@pytest.mark.asyncio
async def test_mock_webhook_valid_signature():
    """Valid webhook signature should pass verification."""
    provider = OfflineMockPaymentProvider()
    payload = b'{"event": "payment.captured", "order_id": "mock_order_123"}'
    signature = hmac.new(
        MOCK_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    assert await provider.verify_webhook_signature(payload, signature) is True


@pytest.mark.asyncio
async def test_mock_webhook_invalid_signature():
    """Tampered webhook signature should be rejected."""
    provider = OfflineMockPaymentProvider()
    payload = b'{"event": "payment.captured", "order_id": "mock_order_123"}'
    tampered_signature = "definitely_not_a_valid_signature"

    assert await provider.verify_webhook_signature(payload, tampered_signature) is False


@pytest.mark.asyncio
async def test_mock_webhook_tampered_payload():
    """A valid signature for a different payload should be rejected."""
    provider = OfflineMockPaymentProvider()
    original_payload = b'{"event": "payment.captured", "amount": 500}'
    signature = hmac.new(
        MOCK_WEBHOOK_SECRET.encode(),
        original_payload,
        hashlib.sha256,
    ).hexdigest()

    tampered_payload = b'{"event": "payment.captured", "amount": 50000}'
    assert await provider.verify_webhook_signature(tampered_payload, signature) is False


@pytest.mark.asyncio
async def test_mock_payment_success():
    """Mock payment should succeed for non-failure payment IDs."""
    provider = OfflineMockPaymentProvider()
    order = await provider.create_order(499.00, "test_receipt_001")
    assert order.order_id.startswith("mock_order_")
    assert order.amount_inr == 499.00

    signature = generate_mock_signature(order.order_id, "pay_success_123")
    result = await provider.verify_payment(order.order_id, "pay_success_123", signature)
    assert result.is_valid is True


@pytest.mark.asyncio
async def test_mock_payment_failure():
    """Mock payment should fail for payment IDs containing 'fail'."""
    provider = OfflineMockPaymentProvider()
    order = await provider.create_order(499.00, "test_receipt_002")

    result = await provider.verify_payment(order.order_id, "pay_fail_123", "any_sig")
    assert result.is_valid is False
    assert "failure" in result.error.lower()
