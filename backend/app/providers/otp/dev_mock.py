"""Dev mock OTP provider — accepts fixed OTP "123456" for local development.

Per DEPLOYMENT.md: "use a fixed test OTP in dev mode — don't burn real SMS credits locally."
"""
import logging

from app.config import settings
from app.providers.otp.base import OTPProvider

logger = logging.getLogger(__name__)


class DevMockOTPProvider(OTPProvider):
    """Mock OTP provider for local development. 
    Accepts the fixed code from settings.DEV_OTP_CODE (default: "123456").
    Never used in production."""

    async def send_otp(self, phone: str) -> bool:
        logger.info(f"[DEV MOCK] OTP 'sent' to {phone}. Use code: {settings.DEV_OTP_CODE}")
        return True

    async def verify_otp(self, phone: str, otp: str) -> bool:
        is_valid = otp == settings.DEV_OTP_CODE
        logger.info(f"[DEV MOCK] OTP verify for {phone}: {'✓' if is_valid else '✗'}")
        return is_valid
