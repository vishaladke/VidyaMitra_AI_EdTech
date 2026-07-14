"""Local filesystem storage mock for development."""
import os
import uuid
from typing import BinaryIO

from app.providers.storage.base import StorageProvider

LOCAL_STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "local_storage")


class LocalMockStorageProvider(StorageProvider):
    """Stores files on the local filesystem for development.
    Files go to backend/local_storage/."""

    def __init__(self):
        os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)

    async def upload(self, file: BinaryIO, key: str, content_type: str = "application/octet-stream") -> str:
        filepath = os.path.join(LOCAL_STORAGE_DIR, key)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(file.read())
        return f"http://localhost:8000/static/{key}"

    async def get_url(self, key: str) -> str:
        return f"http://localhost:8000/static/{key}"

    async def delete(self, key: str) -> bool:
        filepath = os.path.join(LOCAL_STORAGE_DIR, key)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
