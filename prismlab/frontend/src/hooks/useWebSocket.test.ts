import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

describe("useWebSocket", () => {
  it.todo("returns 'connecting' status initially");
  it.todo("returns 'connected' status after WebSocket opens");
  it.todo("returns 'disconnected' status after WebSocket closes");
  it.todo("reconnects with exponential backoff after close");
  it.todo("resets reconnect attempts after successful connection");
  it.todo("cleans up WebSocket on unmount");
});
