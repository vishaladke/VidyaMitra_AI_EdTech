"""Auth service — OTP send/verify, JWT issue, user creation/lookup.

Handles the full auth flow including Super Admin TOTP verification.
Uses dev_mock OTP provider in local environment.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User, UserRole, StudentProfile, TeacherProfile, ParentProfile
from app.providers.otp.base import OTPProvider
from app.providers.otp.dev_mock import DevMockOTPProvider
from app.providers.otp.firebase import FirebaseOTPProvider
from app.providers.otp.msg91 import MSG91OTPProvider
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    create_temp_token,
    generate_totp_secret,
    verify_totp,
)

logger = logging.getLogger(__name__)


def get_otp_provider() -> OTPProvider:
    """Factory: select OTP provider based on config.
    In local env, always use dev_mock regardless of OTP_PROVIDER setting."""
    if settings.ENVIRONMENT == "local":
        return DevMockOTPProvider()

    providers = {
        "dev_mock": DevMockOTPProvider,
        "firebase": FirebaseOTPProvider,
        "msg91": MSG91OTPProvider,
    }
    provider_class = providers.get(settings.OTP_PROVIDER, DevMockOTPProvider)
    return provider_class()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.otp_provider = get_otp_provider()

    async def request_otp(self, phone: str) -> bool:
        """Send OTP to phone number."""
        return await self.otp_provider.send_otp(phone)

    async def verify_otp_and_login(
        self,
        phone: str,
        otp: str,
        full_name: Optional[str] = None,
        role: Optional[str] = None,
        grade: Optional[int] = None,
    ) -> dict:
        """Verify OTP, create user if needed, return tokens.
        
        Returns dict with:
        - access_token, refresh_token, user (if login successful)
        - requires_totp, temp_token (if Super Admin needs TOTP step)
        - requires_registration (if user doesn't exist and no role provided)
        """
        # Verify OTP
        is_valid = await self.otp_provider.verify_otp(phone, otp)
        if not is_valid:
            return {"error": "Invalid OTP"}

        # Look up user
        result = await self.db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()

        # User doesn't exist — need registration info
        if user is None:
            if not full_name or not role:
                return {"requires_registration": True}

            # Create new user
            user_role = UserRole(role)
            user = User(
                phone=phone,
                full_name=full_name,
                role=user_role,
                is_active=True,
            )
            self.db.add(user)
            await self.db.flush()

            # Create role-specific profile
            if user_role == UserRole.STUDENT:
                profile = StudentProfile(
                    user_id=user.id,
                    grade=grade or 5,  # default to grade 5
                )
                self.db.add(profile)
            elif user_role == UserRole.TEACHER:
                profile = TeacherProfile(user_id=user.id)
                self.db.add(profile)
            elif user_role == UserRole.PARENT:
                profile = ParentProfile(user_id=user.id)
                self.db.add(profile)

            # Super Admin gets a TOTP secret
            if user_role == UserRole.SUPER_ADMIN:
                user.totp_secret = generate_totp_secret()

            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"New user created: {phone} as {role}")

        # Check if user is active
        if not user.is_active:
            return {"error": "Account is deactivated"}

        # Super Admin: require TOTP before issuing full tokens
        if user.role == UserRole.SUPER_ADMIN:
            temp_token = create_temp_token(user.id)
            return {
                "requires_totp": True,
                "temp_token": temp_token,
                "totp_setup_needed": not user.totp_verified,
            }

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Issue tokens
        access_token = create_access_token(user.id, user.role.value)
        refresh_token = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": str(user.id),
                "phone": user.phone,
                "email": user.email,
                "role": user.role.value,
                "full_name": user.full_name,
                "is_active": user.is_active,
            },
        }

    async def verify_totp_and_login(self, user: User, totp_code: str) -> dict:
        """Verify TOTP code for Super Admin and issue full tokens."""
        if not user.totp_secret:
            return {"error": "TOTP not set up"}

        if not verify_totp(user.totp_secret, totp_code):
            return {"error": "Invalid TOTP code"}

        # Mark TOTP as verified if first time
        if not user.totp_verified:
            user.totp_verified = True

        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()

        access_token = create_access_token(user.id, user.role.value)
        refresh_token = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": str(user.id),
                "phone": user.phone,
                "email": user.email,
                "role": user.role.value,
                "full_name": user.full_name,
                "is_active": user.is_active,
            },
        }
