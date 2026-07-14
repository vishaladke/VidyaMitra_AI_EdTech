/**
 * JWT authentication middleware for Socket.io connections.
 * Uses the same JWT_SECRET as the Python backend.
 */
import { Socket } from "socket.io";
import jwt from "jsonwebtoken";
import { config } from "../config";

export function verifySocketToken(
  socket: Socket,
  next: (err?: Error) => void
): void {
  const token =
    socket.handshake.auth?.token ||
    socket.handshake.headers?.authorization?.replace("Bearer ", "");

  if (!token) {
    return next(new Error("Authentication required"));
  }

  try {
    const payload = jwt.verify(token, config.jwtSecret) as any;

    if (payload.type !== "access") {
      return next(new Error("Invalid token type"));
    }

    // Attach user info to socket for downstream handlers
    (socket as any).userId = payload.sub;
    (socket as any).userRole = payload.role;
    (socket as any).token = token;  // stored for forwarding to backend API
    next();
  } catch (err) {
    next(new Error("Invalid or expired token"));
  }
}
