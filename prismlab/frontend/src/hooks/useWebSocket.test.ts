import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useWebSocket } from "./useWebSocket";

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  readyState = 0;
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  simulateOpen() {
    this.readyState = 1;
    this.onopen?.();
  }

  simulateClose() {
    this.readyState = 3;
    this.onclose?.();
  }

  simulateMessage(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }
}

describe("useWebSocket", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("returns 'connecting' status initially", () => {
    const { result } = renderHook(() => useWebSocket("ws://localhost/ws"));
    expect(result.current.status).toBe("connecting");
  });

  it("returns 'connected' status after WebSocket opens", () => {
    const { result } = renderHook(() => useWebSocket("ws://localhost/ws"));
    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });
    expect(result.current.status).toBe("connected");
  });

  it("returns 'disconnected' status after WebSocket closes", () => {
    const { result } = renderHook(() => useWebSocket("ws://localhost/ws"));
    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });
    act(() => {
      MockWebSocket.instances[0].simulateClose();
    });
    expect(result.current.status).toBe("disconnected");
  });

  it("reconnects with exponential backoff after close", () => {
    renderHook(() => useWebSocket("ws://localhost/ws"));
    expect(MockWebSocket.instances).toHaveLength(1);

    // First close triggers reconnect after 1s
    act(() => {
      MockWebSocket.instances[0].simulateClose();
    });
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(MockWebSocket.instances).toHaveLength(2);

    // Second close triggers reconnect after 2s
    act(() => {
      MockWebSocket.instances[1].simulateClose();
    });
    act(() => {
      vi.advanceTimersByTime(1500);
    });
    // Should not have reconnected yet (only 1.5s of 2s elapsed)
    expect(MockWebSocket.instances).toHaveLength(2);
    act(() => {
      vi.advanceTimersByTime(500);
    });
    expect(MockWebSocket.instances).toHaveLength(3);
  });

  it("resets reconnect attempts after successful connection", () => {
    renderHook(() => useWebSocket("ws://localhost/ws"));

    // Close and reconnect
    act(() => {
      MockWebSocket.instances[0].simulateClose();
    });
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(MockWebSocket.instances).toHaveLength(2);

    // Open the new connection (resets attempts)
    act(() => {
      MockWebSocket.instances[1].simulateOpen();
    });

    // Close again -- should use 1s delay (reset), not 2s
    act(() => {
      MockWebSocket.instances[1].simulateClose();
    });
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(MockWebSocket.instances).toHaveLength(3);
  });

  it("cleans up WebSocket on unmount", () => {
    const { unmount } = renderHook(() => useWebSocket("ws://localhost/ws"));
    const ws = MockWebSocket.instances[0];
    unmount();
    expect(ws.close).toHaveBeenCalled();
  });
});
