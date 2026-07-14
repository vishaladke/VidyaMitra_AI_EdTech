"""Cloudflare R2 storage provider (S3-compatible). Stub for now."""
import logging
from typing import BinaryIO
from app.providers.storage.base import StorageProvider

logger = logging.getLogger(__name__)


class R2StorageProvider(StorageProvider):
    """Cloudflare R2 — S3-compatible, zero egress fees.
    TODO: Implement with boto3 S3 client pointed at R2 endpoint."""

    async def upload(self, file: BinaryIO, key: str, content_type: str = "application/octet-stream") -> str:
        raise NotImplementedError("R2 storage — implement when R2 credentials are available")

    async def get_url(self, key: str) -> str:
        raise NotImplementedError("R2 storage — implement when R2 credentials are available")

    async def delete(self, key: str) -> bool:
        raise NotImplementedError("R2 storage — implement when R2 credentials are available")
