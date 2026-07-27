"""Webhook router — receives forwarded webhooks from the Node gateway.

Endpoints:
- POST /api/webhooks/whatsapp — WhatsApp delivery receipts + inbound messages
"""
import logging
from typing import Optional

from fastapi import APIRouter, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.dependencies import get_db
from app.providers.notification.whatsapp import WhatsAppProvider
from app.services.notification_service import update_delivery_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Process WhatsApp webhook events forwarded from the Node gateway.

    Handles:
    1. Delivery status updates (sent → delivered → read → failed)
    2. Inbound messages (for future 2-way conversations)

    The Node gateway (whatsapp-webhook.ts) already handles Meta's GET
    verification challenge — this endpoint only receives POST payloads.
    """
    try:
        body = await request.json()
    except Exception:
        logger.warning("[WEBHOOK/WHATSAPP] Invalid JSON payload")
        return {"status": "error", "reason": "invalid_json"}

    # Try to parse as delivery status update
    delivery_status = WhatsAppProvider.parse_delivery_status(body)
    if delivery_status and delivery_status.get("message_id"):
        msg_id = delivery_status["message_id"]
        status = delivery_status.get("status", "unknown")
        timestamp = delivery_status.get("timestamp")

        updated = await update_delivery_status(
            db=db,
            provider_message_id=msg_id,
            status=status,
            timestamp=timestamp,
        )

        logger.info(f"[WEBHOOK/WHATSAPP] Delivery status: {msg_id} → {status} (updated={updated})")
        return {"status": "processed", "type": "delivery_status", "message_id": msg_id}

    # Try to parse as inbound message
    inbound = WhatsAppProvider.parse_inbound_message(body)
    if inbound and inbound.get("from"):
        sender = inbound["from"]
        text = inbound.get("text", "")
        logger.info(f"[WEBHOOK/WHATSAPP] Inbound message from {sender}: {text[:100]}")

        # TODO: Phase 6+ — handle parent replies within 24-hour service window
        # For now, just acknowledge receipt
        return {
            "status": "processed",
            "type": "inbound_message",
            "from": sender,
            "note": "Inbound message handling not yet implemented",
        }

    # Unrecognized payload — acknowledge to prevent retries
    logger.debug(f"[WEBHOOK/WHATSAPP] Unrecognized payload type")
    return {"status": "acknowledged", "type": "unknown"}
