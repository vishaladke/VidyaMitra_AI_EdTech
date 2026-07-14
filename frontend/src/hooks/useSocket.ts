/**
 * Socket.io connection manager hook.
 * Connects to the realtime gateway with JWT auth.
 */
import { useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

const GATEWAY_URL = 'http://localhost:4000';

export function useSocket() {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const socket = io(GATEWAY_URL, {
      auth: { token },
      transports: ['websocket'],
    });

    socket.on('connect', () => setIsConnected(true));
    socket.on('disconnect', () => setIsConnected(false));

    socketRef.current = socket;

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, []);

  return { socket: socketRef.current, isConnected };
}
