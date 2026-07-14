"""Abstract StorageProvider interface for file uploads (R2, local mock)."""
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional


class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, file: BinaryIO, key: str, content_type: str = "application/octet-stream") -> str:
        """Upload a file. Returns the public URL."""
        ...

    @abstractmethod
    async def get_url(self, key: str) -> str:
        """Get the public URL for a file."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a file. Returns True if successful."""
        ...
