import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { useRefreshStore } from "./refreshStore";
import type { TriggerEvent } from "./refreshStore";

describe("refreshStore", () => {
  beforeEach(() => {
    useRefreshStore.setState({
      cooldownEnd: null,
      queuedEvent: null,
      secondsRemaining: 0,
      lastToast: null,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("initializes with default state", () => {
    const state = useRefreshStore.getState();
    expect(state.cooldownEnd).toBeNull();
    expect(state.queuedEvent).toBeNull();
    expect(state.lastToast).toBeNull();
    expect(state.secondsRemaining).toBe(0);
  });

  it("startCooldown sets cooldownEnd to Date.now() + 120000", () => {
    const now = 1700000000000;
    vi.spyOn(Date, "now").mockReturnValue(now);
    useRefreshStore.getState().startCooldown();
    expect(useRefreshStore.getState().cooldownEnd).toBe(now + 120_000);
  });

  it("queueEvent sets queuedEvent to the provided TriggerEvent", () => {
    const event: TriggerEvent = { type: "death", message: "You died" };
    useRefreshStore.getState().queueEvent(event);
    expect(useRefreshStore.getState().queuedEvent).toEqual(event);
  });

  it("queueEvent replaces previous queued event (queue-latest-only)", () => {
    const event1: TriggerEvent = { type: "death", message: "You died" };
    const event2: TriggerEvent = {
      type: "tower_kill",
      message: "Tower destroyed",
    };
    useRefreshStore.getState().queueEvent(event1);
    useRefreshStore.getState().queueEvent(event2);
    expect(useRefreshStore.getState().queuedEvent).toEqual(event2);
  });

  it("clearQueue sets queuedEvent to null", () => {
    const event: TriggerEvent = { type: "death", message: "You died" };
    useRefreshStore.getState().queueEvent(event);
    useRefreshStore.getState().clearQueue();
    expect(useRefreshStore.getState().queuedEvent).toBeNull();
  });

  it("showToast sets lastToast with message and timestamp", () => {
    const now = 1700000000000;
    vi.spyOn(Date, "now").mockReturnValue(now);
    useRefreshStore.getState().showToast("Recommendations updated");
    const toast = useRefreshStore.getState().lastToast;
    expect(toast).toEqual({
      message: "Recommendations updated",
      timestamp: now,
    });
  });

  it("dismissToast sets lastToast to null", () => {
    useRefreshStore.getState().showToast("Recommendations updated");
    useRefreshStore.getState().dismissToast();
    expect(useRefreshStore.getState().lastToast).toBeNull();
  });

  it("tick computes secondsRemaining from cooldownEnd - now, clamped to 0", () => {
    // Set cooldownEnd 60 seconds in the future from "now"
    useRefreshStore.setState({ cooldownEnd: 1700000060000 });
    useRefreshStore.getState().tick(1700000000000);
    expect(useRefreshStore.getState().secondsRemaining).toBe(60);
  });

  it("tick sets secondsRemaining to 0 when no cooldown active", () => {
    useRefreshStore.getState().tick(1700000000000);
    expect(useRefreshStore.getState().secondsRemaining).toBe(0);
  });

  it("tick sets secondsRemaining to 0 when cooldown expired", () => {
    useRefreshStore.setState({ cooldownEnd: 1700000000000 });
    useRefreshStore.getState().tick(1700000120000); // 120s later
    expect(useRefreshStore.getState().secondsRemaining).toBe(0);
  });

  it("tick uses Math.ceil for partial seconds", () => {
    // 59.5 seconds remaining -> should ceil to 60
    useRefreshStore.setState({ cooldownEnd: 1700000059500 });
    useRefreshStore.getState().tick(1700000000000);
    expect(useRefreshStore.getState().secondsRemaining).toBe(60);
  });

  it("resetCooldown clears cooldownEnd, queuedEvent, and secondsRemaining", () => {
    const now = 1700000000000;
    vi.spyOn(Date, "now").mockReturnValue(now);
    useRefreshStore.getState().startCooldown();
    useRefreshStore
      .getState()
      .queueEvent({ type: "death", message: "You died" });
    useRefreshStore.setState({ secondsRemaining: 45 });

    useRefreshStore.getState().resetCooldown();
    const state = useRefreshStore.getState();
    expect(state.cooldownEnd).toBeNull();
    expect(state.queuedEvent).toBeNull();
    expect(state.secondsRemaining).toBe(0);
  });
});
