"""WhatsApp notification provider — BSP integration.

Sends messages via a WhatsApp BSP (AiSensy/Interakt/Gupshup/WATI).
The BSP handles template approval, business verification, and webhook routing.

Per ARCHITECTURE.md §11: WhatsApp is the primary notification channel.
Weekly parent reports use Utility-category templates (low cost, ~₹0.50/msg).

The BSP API is abstracted here so switching providers is a config change.
"""
import json
import logging
import uuid
from typing import Optional

import httpx

from app.config import settings
from app.providers.notification.base import NotificationChannelProvider

logger = logging.getLogger(__name__)

# Template names registered with the WhatsApp BSP
TEMPLATE_WEEKLY_REPORT = "weekly_student_report"
TEMPLATE_PAYMENT_CONFIRMATION = "payment_confirmation"
TEMPLATE_WELCOME = "welcome_parent"


class WhatsAppProvider(NotificationChannelProvider):
    """WhatsApp BSP provider — sends template messages via BSP API.

    Supports both AiSensy-style and generic Cloud API-compatible BSPs.
    The WHATSAPP_BSP_URL and WHATSAPP_BSP_API_KEY in .env control routing.
    """

    def __init__(self) -> None:
        self.api_key = settings.WHATSAPP_BSP_API_KEY
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.bsp_url = getattr(settings, "WHATSAPP_BSP_URL", "")

        if not self.api_key:
            logger.warning(
                "[WHATSAPP] WHATSAPP_BSP_API_KEY not set — "
                "messages will be logged but not sent"
            )

    async def send(
        self, to: str, template_name: str, params: Optional[dict] = None
    ) -> str:
        """Send a WhatsApp template message.

        Args:
            to: Recipient phone number (with country code, e.g., "919999999003")
            template_name: BSP-registered template name
            params: Template variable values

        Returns:
            Provider message ID (for delivery tracking)
        """
        if not self.api_key or not self.bsp_url:
            # Fallback: log the message for dev/staging
            msg_id = f"wa_undelivered_{uuid.uuid4().hex[:8]}"
            logger.info(
                f"[WHATSAPP] (NO BSP CONFIGURED) Would send to={to} "
                f"template={template_name} params={params} msg_id={msg_id}"
            )
            return msg_id

        return await self._send_via_bsp(to, template_name, params)

    async def _send_via_bsp(
        self, to: str, template_name: str, params: Optional[dict] = None
    ) -> str:
        """Send via BSP API (AiSensy/Interakt/Gupshup compatible)."""
        # Normalize phone number — ensure country code, no spaces/dashes
        phone = to.replace(" ", "").replace("-", "").replace("+", "")
        if not phone.startswith("91"):
            phone = f"91{phone}"

        # Build template payload (Cloud API compatible format)
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "mr"},  # Marathi
                "components": [],
            },
        }

        # Add template parameters if provided
        if params:
            body_params = []
            for key, value in params.items():
                body_params.append({
                    "type": "text",
                    "text": str(value),
                })

            if body_params:
                payload["template"]["components"].append({
                    "type": "body",
                    "parameters": body_params,
                })

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.bsp_url}/messages",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    msg_id = data.get("messages", [{}])[0].get("id", f"wa_{uuid.uuid4().hex[:8]}")
                    logger.info(f"[WHATSAPP] Message sent to {phone}: {msg_id}")
                    return msg_id
                else:
                    error_detail = response.text
                    logger.error(f"[WHATSAPP] Failed to send to {phone}: {response.status_code} {error_detail}")
                    return f"wa_error_{uuid.uuid4().hex[:8]}"

        except httpx.TimeoutException:
            logger.error(f"[WHATSAPP] Timeout sending to {phone}")
            return f"wa_timeout_{uuid.uuid4().hex[:8]}"
        except Exception as e:
            logger.error(f"[WHATSAPP] Error sending to {phone}: {e}")
            return f"wa_error_{uuid.uuid4().hex[:8]}"

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language: str = "mr",
        header_params: Optional[list[str]] = None,
        body_params: Optional[list[str]] = None,
    ) -> str:
        """Send a structured template message with explicit header/body params.

        This is the preferred method for sending weekly reports where
        template variable mapping matters.
        """
        params = {}
        if body_params:
            for i, value in enumerate(body_params):
                params[f"body_{i+1}"] = value

        return await self.send(to, template_name, params)

    @staticmethod
    def parse_delivery_status(webhook_body: dict) -> Optional[dict]:
        """Parse delivery status from WhatsApp webhook payload.

        Returns dict with: message_id, status (sent/delivered/read/failed), timestamp
        """
        try:
            entries = webhook_body.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    statuses = value.get("statuses", [])
                    for status in statuses:
                        return {
                            "message_id": status.get("id"),
                            "status": status.get("status"),  # sent, delivered, read, failed
                            "timestamp": status.get("timestamp"),
                            "recipient_id": status.get("recipient_id"),
                            "errors": status.get("errors"),
                        }
        except Exception as e:
            logger.error(f"[WHATSAPP] Error parsing delivery status: {e}")

        return None

    @staticmethod
    def parse_inbound_message(webhook_body: dict) -> Optional[dict]:
        """Parse inbound message from WhatsApp webhook payload.

        For future: handle parent replies within the 24-hour service window.
        """
        try:
            entries = webhook_body.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    for message in messages:
                        return {
                            "message_id": message.get("id"),
                            "from": message.get("from"),
                            "type": message.get("type"),
                            "text": message.get("text", {}).get("body"),
                            "timestamp": message.get("timestamp"),
                        }
        except Exception as e:
            logger.error(f"[WHATSAPP] Error parsing inbound message: {e}")

        return None
