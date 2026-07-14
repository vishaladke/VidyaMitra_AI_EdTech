"""WhatsApp notification provider (stub — BSP integration in Phase 5)."""
import logging
from typing import Optional
from app.providers.notification.base import NotificationChannelProvider

logger = logging.getLogger(__name__)


class WhatsAppProvider(NotificationChannelProvider):
    async def send(self, to: str, template_name: str, params: Optional[dict] = None) -> str:
        logger.warning("[WHATSAPP] Not yet implemented — implement in Phase 5")
        return "not_implemented"
