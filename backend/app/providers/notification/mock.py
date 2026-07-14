"""Mock notification provider for local development."""
import logging
import uuid
from typing import Optional
from app.providers.notification.base import NotificationChannelProvider

logger = logging.getLogger(__name__)


class MockNotificationProvider(NotificationChannelProvider):
    async def send(self, to: str, template_name: str, params: Optional[dict] = None) -> str:
        msg_id = f"mock_{uuid.uuid4().hex[:8]}"
        logger.info(f"[MOCK NOTIFICATION] to={to} template={template_name} params={params} msg_id={msg_id}")
        return msg_id
