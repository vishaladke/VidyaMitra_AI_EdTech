"""Firebase Phone Auth OTP provider (stub — will be implemented when Firebase keys are available)."""
import logging

from app.providers.otp.base import OTPProvider

logger = logging.getLogger(__name__)


class FirebaseOTPProvider(OTPProvider):
    """Firebase Phone Auth provider.
    
    Firebase handles rate-limiting/fraud detection out of the box.
    Requires FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL.
    
    Note: Firebase Phone Auth verification is typically done client-side
    via the Firebase JS SDK. This server-side provider is for verifying
    the resulting ID token.
    """

    async def send_otp(self, phone: str) -> bool:
        # In production, OTP sending happens client-side via Firebase JS SDK
        # Server only verifies the resulting Firebase ID token
        logger.info(f"[FIREBASE] OTP request for {phone} — handled by Firebase JS SDK on client")
        return True

    async def verify_otp(self, phone: str, otp: str) -> bool:
        # In production, 'otp' would be the Firebase ID token
        # Verify it using firebase-admin SDK
        # TODO: Implement firebase-admin token verification
        logger.warning("[FIREBASE] verify_otp not yet implemented — use dev_mock for now")
        return False
