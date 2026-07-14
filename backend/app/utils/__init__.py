"""Security utilities: JWT tokens, TOTP, password hashing."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import pyotp
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Password hashing (not used for OTP-only auth, but available for future use)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT constants
ALGORITHM = "HS256"


def create_access_token(
    user_id: uuid.UUID,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a short-lived JWT access token with user ID and role claims."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Create a longer-lived refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_temp_token(user_id: uuid.UUID) -> str:
    """Create a short-lived temp token for TOTP verification step (Super Admin only).
    Expires in 5 minutes — just enough to complete TOTP entry."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "totp_pending",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])


def generate_totp_secret() -> str:
    """Generate a new TOTP secret for Super Admin 2FA setup."""
    return pyotp.random_base32()


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code against the stored secret."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)  # ±30s tolerance


def get_totp_provisioning_uri(secret: str, phone: str) -> str:
    """Generate a TOTP provisioning URI for QR code display."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=phone, issuer_name="VidyaMitra Admin")
