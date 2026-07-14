"""Auth router — OTP login, TOTP verification, token refresh.

Endpoints:
- POST /api/auth/request-otp
- POST /api/auth/verify-otp
- POST /api/auth/verify-totp  (Super Admin only)
- POST /api/auth/refresh
- GET  /api/auth/me
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.middleware.rate_limiter import rate_limiter
from app.models.user import User
from app.schemas.auth import (
    RefreshTokenRequest,
    RequestOTPRequest,
    RequestOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    VerifyTOTPRequest,
    SetupTOTPResponse,
)
from app.services.auth_service import AuthService
from app.utils.security import create_access_token, create_refresh_token, decode_token, get_totp_provisioning_uri

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/request-otp", response_model=RequestOTPResponse)
async def request_otp(
    body: RequestOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Send an OTP to the provided phone number."""
    await rate_limiter.check_ip_rate_limit(request)

    auth_service = AuthService(db)
    sent = await auth_service.request_otp(body.phone)
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send OTP")

    return RequestOTPResponse()


@router.post("/verify-otp")
async def verify_otp(
    body: VerifyOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Verify OTP and return tokens (or TOTP challenge for Super Admin)."""
    await rate_limiter.check_ip_rate_limit(request)

    auth_service = AuthService(db)
    result = await auth_service.verify_otp_and_login(
        phone=body.phone,
        otp=body.otp,
        full_name=body.full_name,
        role=body.role,
        grade=body.grade,
    )

    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])

    return result


@router.post("/verify-totp")
async def verify_totp(
    body: VerifyTOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Verify TOTP code for Super Admin login (second factor)."""
    # Decode temp token
    try:
        payload = decode_token(body.temp_token)
        if payload.get("type") != "totp_pending":
            raise HTTPException(status_code=401, detail="Invalid temp token")
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired temp token")

    # Rate limit Super Admin login attempts
    await rate_limiter.check_superadmin_login_rate(str(user_id))

    # Look up user
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    auth_service = AuthService(db)
    login_result = await auth_service.verify_totp_and_login(user, body.totp_code)

    if "error" in login_result:
        raise HTTPException(status_code=401, detail=login_result["error"])

    return login_result


@router.post("/refresh")
async def refresh_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a refresh token for a new access token."""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token(user.id, user.role.value)
    return {"access_token": access_token}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return {
        "id": str(current_user.id),
        "phone": current_user.phone,
        "email": current_user.email,
        "role": current_user.role.value,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
    }


@router.get("/totp-setup")
async def get_totp_setup(current_user: User = Depends(get_current_user)):
    """Get TOTP setup info (provisioning URI for QR code). Super Admin only."""
    if current_user.role.value != "super_admin":
        raise HTTPException(status_code=403, detail="TOTP is for Super Admin only")
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP secret not generated")

    uri = get_totp_provisioning_uri(current_user.totp_secret, current_user.phone)
    return SetupTOTPResponse(
        secret=current_user.totp_secret,
        provisioning_uri=uri,
    )
