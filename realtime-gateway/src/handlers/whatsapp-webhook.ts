/**
 * WhatsApp webhook receiver — Express routes.
 *
 * Receives inbound messages from the BSP (AiSensy/Interakt/etc.)
 * and forwards them to the Python backend for processing.
 */
import { Router, Request, Response } from "express";
import { config } from "../config";
import { backendClient } from "../utils/backend-client";

export const whatsappWebhookRouter = Router();

// GET — webhook verification (Meta/BSP sends this to verify the endpoint)
whatsappWebhookRouter.get("/", (req: Request, res: Response) => {
  const mode = req.query["hub.mode"];
  const token = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];

  if (mode === "subscribe" && token === config.whatsappWebhookVerifyToken) {
    console.log("[WhatsApp] Webhook verified");
    res.status(200).send(challenge);
  } else {
    console.warn("[WhatsApp] Webhook verification failed");
    res.sendStatus(403);
  }
});

// POST — inbound messages
whatsappWebhookRouter.post("/", async (req: Request, res: Response) => {
  console.log("[WhatsApp] Inbound webhook:", JSON.stringify(req.body).substring(0, 200));

  try {
    // Forward to Python backend for processing
    await backendClient.post("/api/webhooks/whatsapp", req.body);
    res.sendStatus(200);
  } catch (err) {
    console.error("[WhatsApp] Failed to forward to backend:", err);
    // Still return 200 to WhatsApp to prevent retries
    res.sendStatus(200);
  }
});
