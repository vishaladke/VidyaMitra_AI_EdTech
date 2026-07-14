"""Auth request/response schemas — Pydantic validation on every endpoint."""
from pydantic import BaseModel, Field
from typing import Optional
import uuid


class RequestOTPRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{6,14}$", description="Phone number (E.164 or local)")


class RequestOTPResponse(BaseModel):
    message: str = "OTP sent"
    expires_in: int = 300  # seconds


class VerifyOTPRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{6,14}$")
    otp: str = Field(..., min_length=4, max_length=8)
    # For first-time registration
    full_name: Optional[str] = None
    role: Optional[str] = None  # student, teacher, parent
    grade: Optional[int] = None  # required if role=student


class VerifyOTPResponse(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    requires_totp: bool = False  # True for Super Admin
    temp_token: Optional[str] = None  # Used for TOTP step
    requires_registration: bool = False  # True if user doesn't exist
    user: Optional["UserInfo"] = None


class VerifyTOTPRequest(BaseModel):
    temp_token: str
    totp_code: str = Field(..., min_length=6, max_length=6)


class SetupTOTPResponse(BaseModel):
    secret: str
    provisioning_uri: str
    message: str = "Scan this QR code with your authenticator app"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserInfo(BaseModel):
    id: uuid.UUID
    phone: str
    email: Optional[str] = None
    role: str
    full_name: str
    is_active: bool

    model_config = {"from_attributes": True}


# Fix forward reference
VerifyOTPResponse.model_rebuild()
