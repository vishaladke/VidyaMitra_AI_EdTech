"""MSG91 OTP provider (stub)."""
import logging
from app.providers.otp.base import OTPProvider

logger = logging.getLogger(__name__)


class MSG91OTPProvider(OTPProvider):
    """MSG91 OTP provider — India-specific alternative to Firebase.
    TODO: Implement when MSG91_AUTH_KEY is available."""

    async def send_otp(self, phone: str) -> bool:
        logger.warning("[MSG91] send_otp not yet implemented — use dev_mock for now")
        return False

    async def verify_otp(self, phone: str, otp: str) -> bool:
        logger.warning("[MSG91] verify_otp not yet implemented — use dev_mock for now")
        return False
