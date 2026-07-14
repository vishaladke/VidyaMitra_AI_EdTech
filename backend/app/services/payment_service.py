"""Payment service — provider factory. Full implementation in Phase 5."""
from app.config import settings
from app.providers.payment.base import PaymentProvider
from app.providers.payment.offline_mock import OfflineMockPaymentProvider
from app.providers.payment.razorpay_test import RazorpayTestProvider
from app.providers.payment.razorpay_live import RazorpayLiveProvider


def get_payment_provider() -> PaymentProvider:
    """Factory: select payment provider based on PAYMENT_PROVIDER env var."""
    providers = {
        "offline_mock": OfflineMockPaymentProvider,
        "razorpay_test": RazorpayTestProvider,
        "razorpay_live": RazorpayLiveProvider,
    }
    provider_class = providers.get(settings.PAYMENT_PROVIDER, OfflineMockPaymentProvider)
    return provider_class()
