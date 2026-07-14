"""Auth endpoint tests."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_request_otp(client: AsyncClient):
    """OTP request should succeed for a valid phone number."""
    response = await client.post("/api/auth/request-otp", json={"phone": "9999999999"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "OTP sent"
    assert data["expires_in"] == 300


@pytest.mark.asyncio
async def test_request_otp_invalid_phone(client: AsyncClient):
    """OTP request should fail for invalid phone format."""
    response = await client.post("/api/auth/request-otp", json={"phone": "123"})
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_verify_otp_invalid(client: AsyncClient):
    """Invalid OTP should be rejected."""
    response = await client.post("/api/auth/verify-otp", json={
        "phone": "9999999999",
        "otp": "999999",  # wrong OTP
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_otp_correct_new_user_requires_registration(client: AsyncClient):
    """Correct OTP for non-existent user should ask for registration info."""
    response = await client.post("/api/auth/verify-otp", json={
        "phone": "9999999999",
        "otp": "123456",  # dev mock OTP
    })
    assert response.status_code == 200
    data = response.json()
    assert data.get("requires_registration") is True


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    """/me should return 401 without a token."""
    response = await client.get("/api/auth/me")
    assert response.status_code in (401, 403)
