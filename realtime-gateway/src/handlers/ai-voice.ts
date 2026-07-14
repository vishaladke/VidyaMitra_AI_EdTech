/**
 * AI Voice Socket.io handler — push-to-talk audio.
 * Stub for Phase 2.
 *
 * Per ARCHITECTURE.md §7: Build voice as push-to-talk
 * (record → transcribe → respond → speak) rather than full-duplex
 * for v1 — dramatically simpler and cheaper.
 */
import { Socket, Server } from "socket.io";

export function handleAIVoice(socket: Socket, io: Server): void {
  socket.on("ai:voice:audio", async (data: { audio: Buffer; subjectId?: string }) => {
    console.log(`[AI Voice] Received audio from user ${(socket as any).userId}`);

    // Phase 2: Sarvam Saaras (STT) → Claude → Sarvam Bulbul (TTS)
    socket.emit("ai:voice:response", {
      text: "Voice AI Guru is coming in Phase 2! 🎤",
      audioUrl: null,
      isComplete: true,
    });
  });
}
