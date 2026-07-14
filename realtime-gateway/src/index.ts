/**
 * VidyaMitra Realtime Gateway
 *
 * Thin Node.js layer in front of the Python backend:
 * - Socket.io: AI chat streaming, AI voice (push-to-talk)
 * - Express: WhatsApp webhook receiver
 *
 * Per ARCHITECTURE.md §3: Node handles long-lived socket connections
 * and webhook fan-in — Python backend handles all business logic.
 */
import express from "express";
import { createServer } from "http";
import { Server } from "socket.io";
import cors from "cors";
import dotenv from "dotenv";

import { config } from "./config";
import { verifySocketToken } from "./middleware/auth";
import { handleAIChat } from "./handlers/ai-chat";
import { handleAIVoice } from "./handlers/ai-voice";
import { whatsappWebhookRouter } from "./handlers/whatsapp-webhook";

dotenv.config();

const app = express();
const httpServer = createServer(app);

// CORS
app.use(
  cors({
    origin: config.corsOrigins,
    credentials: true,
  })
);
app.use(express.json());

// ── Express Routes ──────────────────────────────────────
app.get("/health", (_req, res) => {
  res.json({ status: "healthy", service: "vidyamitra-realtime-gateway" });
});

// WhatsApp webhook receiver
app.use("/webhooks/whatsapp", whatsappWebhookRouter);

// ── Socket.io ───────────────────────────────────────────
const io = new Server(httpServer, {
  cors: {
    origin: config.corsOrigins,
    credentials: true,
  },
});

// JWT authentication middleware for Socket.io
io.use(verifySocketToken);

io.on("connection", (socket) => {
  console.log(
    `🔌 Client connected: ${socket.id} (user: ${(socket as any).userId}, role: ${(socket as any).userRole})`
  );

  // AI Chat handlers (Phase 2)
  handleAIChat(socket, io);

  // AI Voice handlers (Phase 2)
  handleAIVoice(socket, io);

  socket.on("disconnect", () => {
    console.log(`🔌 Client disconnected: ${socket.id}`);
  });
});

// ── Start Server ────────────────────────────────────────
const PORT = config.port;
httpServer.listen(PORT, () => {
  console.log(`🚀 VidyaMitra Realtime Gateway running on port ${PORT}`);
  console.log(`   Backend URL: ${config.backendUrl}`);
});
