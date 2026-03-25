import { useState, useEffect, useRef, useCallback } from "react";

interface UseWebSocketReturn {
  status: "connected" | "disconnected" | "connecting";
  lastMessage: unknown | null;
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [status, setStatus] = useState<
    "connected" | "disconnected" | "connecting"
  >("disconnected");
  const [lastMessage, setLastMessage] = useState<unknown | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const unmountedRef = useRef(false);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (unmountedRef.current) return;
    setStatus("connecting");
    const ws = new WebSocket(url);

    ws.onopen = () => {
      if (unmountedRef.current) {
        ws.close();
        return;
      }
      setStatus("connected");
      reconnectAttemptRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch {
        /* ignore malformed messages */
      }
    };

    ws.onclose = () => {
      if (unmountedRef.current) return;
      setStatus("disconnected");
      // Exponential backoff: 1s, 2s, 4s, 8s, max 10s
      const delay = Math.min(
        1000 * 2 ** reconnectAttemptRef.current,
        10000,
      );
      reconnectAttemptRef.current += 1;
      reconnectTimerRef.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      // onclose will fire after onerror, triggering reconnect
    };

    wsRef.current = ws;
  }, [url]);

  useEffect(() => {
    unmountedRef.current = false;
    connect();
    return () => {
      unmountedRef.current = true;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  return { status, lastMessage };
}
