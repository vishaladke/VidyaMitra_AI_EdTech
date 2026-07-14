/**
 * AI Chat Socket.io handler — streams AI responses to students.
 *
 * Flow:
 * 1. Client sends `ai:chat:send` with message + optional conversationId/subjectId
 * 2. Gateway forwards to Python backend POST /api/ai/chat
 * 3. Response is sent back as `ai:chat:chunk` events (for streaming)
 * 4. Final `ai:chat:complete` event signals end of response
 * 5. Safety flags (distress detection) trigger `ai:chat:safety` event
 */
import { Socket, Server } from "socket.io";
import { backendClient } from "../utils/backend-client";

interface ChatSendData {
  message: string;
  conversationId?: string;
  subjectId?: string;
}

interface ChatResponse {
  response: string;
  conversation_id: string;
  message_id: string;
  cache_source: string;
  is_flagged: boolean;
  safety_message?: string;
  cost?: {
    input_tokens: number;
    output_tokens: number;
    cost_inr: number;
    model_used: string;
  };
}

export function handleAIChat(socket: Socket, io: Server): void {
  socket.on("ai:chat:send", async (data: ChatSendData) => {
    const userId = (socket as any).userId;
    const userToken = (socket as any).token;

    if (!data.message || data.message.trim().length === 0) {
      socket.emit("ai:chat:error", {
        error: "Message cannot be empty",
      });
      return;
    }

    // Truncate overly long messages (max 2000 chars)
    const message = data.message.substring(0, 2000);

    console.log(
      `[AI Chat] User ${userId}: ${message.substring(0, 50)}${message.length > 50 ? "..." : ""}`
    );

    // Emit typing indicator
    socket.emit("ai:chat:typing", { isTyping: true });

    try {
      // Forward to Python backend AI service
      const response = await backendClient.post<ChatResponse>(
        "/api/ai/chat",
        {
          message: message,
          conversation_id: data.conversationId || null,
          subject_id: data.subjectId || null,
        },
        {
          headers: {
            Authorization: `Bearer ${userToken}`,
          },
          timeout: 30000, // 30s timeout for AI responses
        }
      );

      const result = response.data;

      // Check for safety flag first
      if (result.is_flagged) {
        socket.emit("ai:chat:safety", {
          conversationId: result.conversation_id,
          safetyMessage: result.safety_message,
        });
        console.log(
          `[AI Chat] ⚠️ SAFETY FLAG for user ${userId} in conversation ${result.conversation_id}`
        );
      }

      // Simulate streaming by sending chunks
      // For cache hits, response is instant — send as one chunk
      // For LLM responses, we could potentially stream, but the current
      // backend returns the full response at once
      const content = result.response;
      const chunkSize = 50; // characters per chunk for simulated streaming
      const isCacheHit = result.cache_source !== "live_llm";

      if (isCacheHit) {
        // Cache hits: send full response immediately
        socket.emit("ai:chat:chunk", {
          content: content,
          conversationId: result.conversation_id,
          isComplete: false,
        });
      } else {
        // LLM responses: simulate streaming for better UX
        for (let i = 0; i < content.length; i += chunkSize) {
          const chunk = content.substring(i, i + chunkSize);
          socket.emit("ai:chat:chunk", {
            content: chunk,
            conversationId: result.conversation_id,
            isComplete: false,
          });
          // Small delay between chunks for streaming effect
          await new Promise((resolve) => setTimeout(resolve, 30));
        }
      }

      // Send completion event
      socket.emit("ai:chat:complete", {
        conversationId: result.conversation_id,
        messageId: result.message_id,
        cacheSource: result.cache_source,
        isFlagged: result.is_flagged,
        cost: result.cost || null,
      });

      console.log(
        `[AI Chat] ✅ Response sent to user ${userId} (source: ${result.cache_source})`
      );
    } catch (error: any) {
      console.error(`[AI Chat] ❌ Error for user ${userId}:`, error.message);

      // Stop typing indicator
      socket.emit("ai:chat:typing", { isTyping: false });

      // Determine error type
      if (error.response?.status === 401) {
        socket.emit("ai:chat:error", {
          error: "Session expired. Please log in again.",
          code: "AUTH_ERROR",
        });
      } else if (error.response?.status === 429) {
        socket.emit("ai:chat:error", {
          error: "Too many questions! Please wait a moment.",
          code: "RATE_LIMIT",
        });
      } else if (error.code === "ECONNABORTED") {
        socket.emit("ai:chat:error", {
          error:
            "AI Guru is taking too long. Please try again.",
          code: "TIMEOUT",
        });
      } else {
        socket.emit("ai:chat:error", {
          error:
            "Something went wrong. Please try again.",
          code: "INTERNAL_ERROR",
        });
      }
    } finally {
      // Always stop typing indicator
      socket.emit("ai:chat:typing", { isTyping: false });
    }
  });

  // Conversation history request
  socket.on("ai:conversations:list", async (data: { limit?: number; offset?: number }) => {
    const userToken = (socket as any).token;

    try {
      const response = await backendClient.get("/api/ai/conversations", {
        headers: { Authorization: `Bearer ${userToken}` },
        params: { limit: data.limit || 20, offset: data.offset || 0 },
      });

      socket.emit("ai:conversations:list", {
        conversations: response.data,
      });
    } catch (error: any) {
      socket.emit("ai:chat:error", {
        error: "Failed to load conversations.",
        code: "FETCH_ERROR",
      });
    }
  });
}
