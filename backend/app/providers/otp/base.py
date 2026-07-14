"""Abstract base class for OTP providers."""
from abc import ABC, abstractmethod


class OTPProvider(ABC):
    """Interface for OTP providers (Firebase, MSG91, dev mock)."""

    @abstractmethod
    async def send_otp(self, phone: str) -> bool:
        """Send an OTP to the given phone number.
        Returns True if sent successfully."""
        ...

    @abstractmethod
    async def verify_otp(self, phone: str, otp: str) -> bool:
        """Verify the OTP for the given phone number.
        Returns True if the OTP is valid."""
        ...
